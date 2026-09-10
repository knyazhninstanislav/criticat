# app/telegram_poller.py
import asyncio
import logging
import threading
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Optional

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, TimedOut, NetworkError, RetryAfter

from .config import settings
from .rabbitmq_client import rabbitmq_client
from .telegram_bot import TelegramBot
from .result_service import ResultService
from .database import AnonymizedResult

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'ok',
                'poller': 'running',
                'rabbitmq': 'connected' if rabbitmq_client.is_connected() else 'disconnected',
                'telegram': 'checking'
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class TelegramPoller:
    """Poller для обработки callback от Telegram"""

    def __init__(self):
        self.telegram_bot = TelegramBot(settings.telegram_token)
        self.health_server = None
        self.running = False
        self._telegram_available = False

    def start_health_server(self):
        try:
            self.health_server = HTTPServer(('0.0.0.0', 8081), HealthHandler)
            thread = threading.Thread(target=self.health_server.serve_forever, daemon=True)
            thread.start()
            logger.info("Health check на порту 8081")
        except Exception as e:
            logger.error(f"Ошибка health check: {e}")

    async def check_telegram_connection(self) -> bool:
        """Проверка доступности Telegram API"""
        if not self.telegram_bot.bot:
            return False

        try:
            # Пробуем получить информацию о боте
            me = await asyncio.wait_for(
                self.telegram_bot.bot.get_me(),
                timeout=10.0
            )
            logger.info(f"Telegram доступен: @{me.username}")
            return True
        except asyncio.TimeoutError:
            logger.warning("Telegram API: таймаут подключения")
            return False
        except (TimedOut, NetworkError) as e:
            logger.warning(f"Telegram API недоступен: {e}")
            return False
        except TelegramError as e:
            logger.warning(f"Telegram API ошибка: {e}")
            return False
        except Exception as e:
            logger.warning(f"Ошибка проверки Telegram: {e}")
            return False

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback"""
        try:
            query = update.callback_query
            data = query.data
            chat_id = str(query.message.chat_id)
            message_id = str(query.message.message_id)

            logger.info(f"Callback: {data} от {chat_id}")

            # Отвечаем на callback сразу (чтобы убрать "часики")
            try:
                await query.answer()
            except Exception as e:
                logger.warning(f"Не удалось ответить на callback: {e}")

            # Обработка Approve All
            if data.startswith("approve_all:"):
                ids_str = data[12:]
                result_ids = [int(x) for x in ids_str.split(',') if x.strip()]

                for result_id in result_ids:
                    await self._send_user_response(result_id, chat_id, 'approved')

                await self._update_message_after_response(
                    chat_id, message_id, result_ids, 'approved'
                )

            # Обработка Approve Single
            elif data.startswith("approve:"):
                result_id = int(data[8:])
                await self._send_user_response(result_id, chat_id, 'approved')
                await self._update_message_after_response(
                    chat_id, message_id, [result_id], 'approved'
                )

            # Обработка Reject
            elif data.startswith("reject:"):
                result_id = int(data[7:])
                await self._send_user_response(result_id, chat_id, 'rejected')
                await self._update_message_after_response(
                    chat_id, message_id, [result_id], 'rejected'
                )

            else:
                logger.warning(f"Неизвестная команда: {data}")

        except Exception as e:
            logger.error(f"Ошибка callback: {e}", exc_info=True)

    async def _send_user_response(self, result_id: int, chat_id: str, action: str):
        """Отправка ответа пользователя в RabbitMQ"""
        service = ResultService()
        try:
            result = service.db.query(AnonymizedResult).filter(
                AnonymizedResult.id == result_id
            ).first()

            if result:
                response_data = {
                    'result_id': result.id,
                    'result_key': result.result_key,
                    'ids': result.ids,
                    'department': result.department,
                    'test_name': result.test_name,
                    'result_value': result.result_value,
                    'action': action,
                    'chat_id': chat_id,
                    'timestamp': datetime.utcnow().isoformat()
                }

                await rabbitmq_client.publish('response.processed', response_data)
                logger.info(f"User response sent: {action} {result.result_key}")
            else:
                logger.warning(f"Result {result_id} not found")

        except Exception as e:
            logger.error(f"Error sending user response: {e}", exc_info=True)
        finally:
            service.close()

    async def _update_message_after_response(
            self,
            chat_id: str,
            message_id: str,
            result_ids: List[int],
            action: str
    ):
        """Обновление сообщения после ответа"""
        try:
            service = ResultService()

            results = service.db.query(AnonymizedResult).filter(
                AnonymizedResult.id.in_(result_ids)
            ).all()

            if results:
                first_result = results[0]
                updated_text = self._format_updated_message(
                    first_result.ids,
                    first_result.department,
                    results,
                    action
                )
                updated_keyboard = self._create_updated_keyboard(results, result_ids)

                # Пытаемся обновить сообщение, но не падаем если Telegram недоступен
                try:
                    await self.telegram_bot.edit_message(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=updated_text,
                        reply_markup=updated_keyboard
                    )
                    logger.info(f"Сообщение {message_id} обновлено")
                except (TimedOut, NetworkError) as e:
                    logger.warning(f"Не удалось обновить сообщение (Telegram недоступен): {e}")
                except TelegramError as e:
                    logger.warning(f"Ошибка Telegram при обновлении: {e}")

            service.close()

        except Exception as e:
            logger.error(f"Error updating message: {e}", exc_info=True)

    def _format_updated_message(self, ids: int, department: str, results: List, action: str):
        """Форматирование обновленного сообщения"""
        message = f"🚨 <b>КРИТИЧЕСКОЕ ОТКЛОНЕНИЕ!</b>\n\n"
        message += f"🆔 <b>IDS:</b> {ids}\n"
        message += f"🏥 <b>Отделение:</b> {department}\n\n"
        message += "<b>Результаты:</b>\n"

        action_text = "✅ ПРИНЯТ" if action == 'approved' else "❌ ОТКЛОНЕН"

        for i, result in enumerate(results, 1):
            message += f"\n{i}. 🧪 <b>{result.test_name}</b>\n"
            message += f"   Значение: <b>{result.result_value:.2f}</b>\n"

            if result.ref_lower and result.ref_upper:
                message += f"   Норма: {result.ref_lower:.2f} - {result.ref_upper:.2f}\n"

            if result.deviation_percent:
                message += f"   Отклонение: <b>{result.deviation_percent:.1f}%</b>\n"

            message += f"   <i>{action_text}</i>\n"

        return message

    def _create_updated_keyboard(self, results: List, processed_ids: List[int]):
        """Создание обновленной клавиатуры"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = []
        processed_set = set(processed_ids)

        for result in results:
            if result.id not in processed_set:
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ {result.test_name[:20]}",
                        callback_data=f"approve:{result.id}"
                    ),
                    InlineKeyboardButton(
                        f"❌ Отклонить",
                        callback_data=f"reject:{result.id}"
                    )
                ])

        if not keyboard:
            keyboard.append([
                InlineKeyboardButton(
                    "✅ Все результаты обработаны",
                    callback_data="all_done"
                )
            ])

        return InlineKeyboardMarkup(keyboard)

    async def run_with_retry(self):
        """Запуск polling с retry-логикой"""
        retry_delay = 5
        max_retry_delay = 300  # максимум 5 минут

        while self.running:
            try:
                # Проверяем доступность Telegram
                self._telegram_available = await self.check_telegram_connection()

                if not self._telegram_available:
                    logger.warning(f"Telegram недоступен, повтор через {retry_delay}с...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                    continue

                # Сбрасываем задержку при успехе
                retry_delay = 5

                # Регистрируем обработчики
                self.telegram_bot.register_handlers_sync(self.handle_callback)
                logger.info("Telegram Poller запущен, начинаем polling...")

                # Запускаем polling
                try:
                    await self.telegram_bot.application.initialize()
                    await self.telegram_bot.application.start()
                    await self.telegram_bot.application.updater.start_polling(
                        drop_pending_updates=True
                    )

                    # Держим polling активным
                    while self.running and self._telegram_available:
                        await asyncio.sleep(10)

                        # Периодически проверяем доступность
                        self._telegram_available = await self.check_telegram_connection()
                        if not self._telegram_available:
                            logger.warning("Telegram стал недоступен, переподключение...")
                            break

                except Exception as e:
                    logger.error(f"Ошибка polling: {e}", exc_info=True)
                finally:
                    try:
                        if self.telegram_bot.application.updater.running:
                            await self.telegram_bot.application.updater.stop()
                        if self.telegram_bot.application.running:
                            await self.telegram_bot.application.stop()
                        await self.telegram_bot.application.shutdown()
                    except Exception as e:
                        logger.warning(f"Ошибка при остановке: {e}")

            except asyncio.CancelledError:
                logger.info("Poller остановлен")
                break
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

    def start(self):
        """Запуск polling"""
        if not self.telegram_bot.application:
            logger.error("Бот не инициализирован - проверьте TELEGRAM_TOKEN")
            return

        self.running = True
        logger.info("Запуск Telegram Poller...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.run_with_retry())
        except KeyboardInterrupt:
            logger.info("Poller остановлен пользователем")
            self.running = False
        finally:
            loop.close()


def main():
    poller = TelegramPoller()
    poller.start_health_server()
    poller.start()


if __name__ == "__main__":
    main()