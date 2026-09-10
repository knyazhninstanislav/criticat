# app/workers.py
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from .config import settings
from .database import init_db, AnonymizedResult
from .rabbitmq_client import rabbitmq_client
from .telegram_bot import TelegramBot
from .message_handlers import MessageHandlers
from .result_service import ResultService
from .models import ResultStatus

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """Healthcheck handler"""

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'ok',
                'service': 'worker',
                'rabbitmq': 'connected' if rabbitmq_client.is_connected() else 'disconnected'
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def start_health_server(port: int = 8080):
    """Запуск healthcheck сервера"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"Healthcheck worker запущен на порту {port}")
        return server
    except Exception as e:
        logger.error(f"Ошибка healthcheck: {e}")
        return None


class ResultWorker:
    """Worker для обработки результатов"""

    def __init__(self):
        self.telegram_bot = TelegramBot(settings.telegram_token)
        self.handlers = MessageHandlers(self.telegram_bot)
        self.running = True
        self._health_server = None

    async def start(self):
        """Запуск worker"""
        logger.info("=" * 60)
        logger.info("WORKER ЗАПУЩЕН")
        logger.info(f"Telegram token: {'настроен' if settings.telegram_token else 'НЕ НАСТРОЕН'}")
        logger.info(f"База данных: {settings.database_url}")
        logger.info(f"RabbitMQ: {settings.rabbitmq_host}:{settings.rabbitmq_port}")
        logger.info("=" * 60)

        # Инициализация БД
        init_db()

        # Подключение к RabbitMQ
        if not await rabbitmq_client.connect():
            logger.error("Не удалось подключиться к RabbitMQ")
            return

        # Запускаем consumers
        await self._setup_consumers()

        # Запускаем фоновые задачи
        await asyncio.gather(
            self._process_pending_timeouts(),
            self._process_expired_confirmations(),
        )

    async def _setup_consumers(self):
        """Настройка consumers"""
        consumers = [
            (settings.queue_incoming, self.handlers.handle_incoming_result),
            (settings.queue_telegram, self.handlers.handle_alert_telegram),
            (settings.queue_app, self.handlers.handle_alert_telegram),  # Можно использовать тот же обработчик
            (settings.queue_response, self.handlers.handle_user_response),
            (settings.queue_rejected, self.handlers.handle_rejected_result),
            (settings.queue_desktop_confirmation, self.handlers.handle_desktop_confirmation),
        ]

        for queue_name, handler in consumers:
            asyncio.create_task(rabbitmq_client.consume(queue_name, handler))
            logger.info(f"Consumer started for {queue_name}")

    async def _process_pending_timeouts(self):
        """Проверка просроченных результатов"""
        while self.running:
            try:
                service = ResultService()

                # Получаем отправленные результаты старше N часов
                timeout = datetime.utcnow() - timedelta(hours=settings.pending_timeout_hours)

                pending_results = service.db.query(AnonymizedResult).filter(
                    AnonymizedResult.status == ResultStatus.SENT.value,
                    AnonymizedResult.created_at < timeout
                ).all()

                for result in pending_results:
                    logger.info(f"Result {result.result_key} expired (timeout)")

                    # Отмечаем как просроченный
                    service.mark_as_expired(result.id)

                    # Отправляем в очередь отклоненных
                    rejected_data = {
                        'result_id': result.id,
                        'result_key': result.result_key,
                        'reason': 'timeout - user did not respond',
                        'rejected_at': datetime.utcnow().isoformat()
                    }
                    await rabbitmq_client.publish('result.rejected', rejected_data)

                service.close()

            except Exception as e:
                logger.error(f"Error processing pending timeouts: {e}", exc_info=True)

            await asyncio.sleep(60)  # Проверяем каждую минуту

    async def _process_expired_confirmations(self):
        """Обработка просроченных подтверждений"""
        while self.running:
            try:
                service = ResultService()

                # Получаем подтвержденные результаты старше 1 часа, которые не были подтверждены десктопом
                cutoff = datetime.utcnow() - timedelta(hours=1)

                confirmed_results = service.db.query(AnonymizedResult).filter(
                    AnonymizedResult.status == ResultStatus.CONFIRMED.value,
                    AnonymizedResult.acknowledged == False,
                    AnonymizedResult.confirmed_at < cutoff
                ).all()

                for result in confirmed_results:
                    # Повторно отправляем подтверждение на десктоп
                    confirmation_data = {
                        'result_id': result.id,
                        'result_key': result.result_key,
                        'action': 'approved',
                        'confirmed_by': result.confirmed_by,
                        'confirmed_at': result.confirmed_at.isoformat() if result.confirmed_at else None
                    }
                    await rabbitmq_client.publish('desktop.confirmation', confirmation_data)
                    logger.info(f"Resent confirmation for {result.result_key}")

                service.close()

            except Exception as e:
                logger.error(f"Error processing expired confirmations: {e}", exc_info=True)

            await asyncio.sleep(300)  # Проверяем каждые 5 минут

    def stop(self):
        """Остановка worker"""
        self.running = False
        logger.info("Worker остановлен")


def main():
    """Основная функция"""
    # Запускаем healthcheck сервер
    health_server = start_health_server(8080)

    # Создаем и запускаем worker
    worker = ResultWorker()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(worker.start())
    except KeyboardInterrupt:
        logger.info("Worker остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        worker.stop()
        loop.close()


if __name__ == "__main__":
    main()