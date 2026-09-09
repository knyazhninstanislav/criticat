# telegram_bot.py
import logging
from typing import List, Dict, Any, Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.error import TelegramError, TimedOut, NetworkError, RetryAfter
import asyncio

from .rabbitmq_client import rabbitmq_client
from .result_service import ResultService

logger = logging.getLogger(__name__)


class TelegramBot:
    """Класс для работы с Telegram ботом"""

    def __init__(self, token: str):
        self.token = token
        self.bot = None
        self.application = None
        self.last_error = None

        if token:
            try:
                self.bot = Bot(token=token)
                self.application = Application.builder().token(token).build()
                logger.info("Telegram Bot инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации: {e}")
        else:
            logger.warning("Токен Telegram не указан")

    async def send_message(
            self,
            chat_id: str,
            text: str,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            parse_mode: str = 'HTML'
    ) -> Optional[str]:
        """Отправка сообщения"""
        if not self.bot:
            return None

        try:
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )

            self.last_error = None
            return str(sent_message.message_id)

        except RetryAfter as e:
            self.last_error = f"Retry after {e.retry_after}s"
            await asyncio.sleep(e.retry_after)
            return None
        except (TimedOut, NetworkError) as e:
            self.last_error = str(e)
            return None
        except TelegramError as e:
            self.last_error = str(e)
            return None
        except Exception as e:
            self.last_error = str(e)
            return None

    async def edit_message(
            self,
            chat_id: str,
            message_id: str,
            text: str,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            parse_mode: str = 'HTML'
    ) -> bool:
        """Редактирование сообщения"""
        if not self.bot:
            return False

        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=int(message_id),
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка редактирования: {e}")
            return False

    async def send_notification(
            self,
            chat_id: str,
            ids: int,
            department: str,
            results: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Отправка уведомления"""
        message = self._format_notification_message(ids, department, results)
        reply_markup = self._create_notification_keyboard(results)

        return await self.send_message(chat_id, message, reply_markup)

    def _format_notification_message(
            self,
            ids: int,
            department: str,
            results: List[Dict[str, Any]]
    ) -> str:
        """Форматирование сообщения"""
        message = f"🚨 <b>КРИТИЧЕСКОЕ ОТКЛОНЕНИЕ!</b>\n\n"
        message += f"🆔 <b>IDS:</b> {ids}\n"
        message += f"🏥 <b>Отделение:</b> {department}\n\n"
        message += "<b>Результаты:</b>\n"

        for i, result in enumerate(results, 1):
            message += f"\n{i}. 🧪 <b>{result.get('test_name', 'Неизвестный тест')}</b>\n"
            message += f"   Значение: <b>{result.get('result_value', 0):.2f}</b>\n"

            if result.get('ref_lower') and result.get('ref_upper'):
                message += f"   Норма: {result.get('ref_lower'):.2f} - {result.get('ref_upper'):.2f}\n"

            if result.get('deviation_percent'):
                message += f"   Отклонение: <b>{result.get('deviation_percent'):.1f}%</b>\n"

        message += "\n⚠️ <i>Нажмите кнопку для подтверждения или отклонения</i>"

        return message

    def _create_notification_keyboard(
            self,
            results: List[Dict[str, Any]]
    ) -> InlineKeyboardMarkup:
        """Создание клавиатуры"""
        keyboard = []

        # Кнопка "Принять все"
        if len(results) > 1:
            result_ids = ','.join(str(r.get('result_id', '')) for r in results if r.get('result_id'))
            if result_ids:
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ Принять все ({len(results)})",
                        callback_data=f"approve_all:{result_ids}"
                    )
                ])

        # Кнопки для каждого результата
        for i, result in enumerate(results[:10], 1):
            result_id = result.get('result_id')
            test_name = result.get('test_name', f'Тест {i}')

            if result_id:
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ {i}. {test_name[:20]}",
                        callback_data=f"approve:{result_id}"
                    ),
                    InlineKeyboardButton(
                        f"❌ Отклонить",
                        callback_data=f"reject:{result_id}"
                    )
                ])

        return InlineKeyboardMarkup(keyboard)

    def register_handlers_sync(self, callback_handler):
        """Регистрация обработчиков"""
        if not self.application:
            return

        self.application.add_handler(CallbackQueryHandler(callback_handler))
        self.application.add_handler(CommandHandler("start", self._start_command))

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id

        welcome_text = (
            f"👋 Здравствуйте, {user.full_name if user else 'пользователь'}!\n\n"
            f"Ваш Chat ID: <code>{chat_id}</code>\n\n"
            f"Вы будете получать уведомления о критических отклонениях.\n"
            f"Для подтверждения результатов используйте кнопки под сообщениями."
        )

        await update.message.reply_text(welcome_text, parse_mode='HTML')