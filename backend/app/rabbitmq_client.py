# app/rabbitmq_client.py
import aio_pika
import json
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Клиент для работы с RabbitMQ с автоматическим переподключением"""

    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self._consumers: Dict[str, Callable] = {}
        self._is_connected = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._consumers_to_restore: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Подключение к RabbitMQ с реконнектом"""
        async with self._lock:
            if self._is_connected and self.connection and not self.connection.is_closed:
                return True

            try:
                url = f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}@" \
                      f"{settings.rabbitmq_host}:{settings.rabbitmq_port}/{settings.rabbitmq_vhost}"

                logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_host}:{settings.rabbitmq_port}")

                # connect_robust автоматически переподключается
                self.connection = await aio_pika.connect_robust(
                    url,
                    reconnect_interval=5,  # попытка каждые 5 секунд
                    fail_fast=False,  # не падать сразу, пытаться подключиться
                )

                # Регистрируем callbacks для отслеживания состояния
                self.connection.reconnect_callbacks.add(self._on_reconnect)
                self.connection.close_callbacks.add(self._on_close)

                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=1)

                await self._setup_queues_and_exchanges()

                self._is_connected = True
                logger.info("✅ Connected to RabbitMQ successfully")

                # Восстанавливаем consumers, если были
                await self._restore_consumers()

                return True

            except Exception as e:
                self._is_connected = False
                logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
                return False

    def _on_reconnect(self, connection):
        """Callback при переподключении"""
        logger.info("🔄 RabbitMQ reconnected")
        self._is_connected = True
        # Восстанавливаем consumers в фоне
        asyncio.create_task(self._restore_consumers())

    def _on_close(self, connection, exc):
        """Callback при закрытии соединения"""
        logger.warning(f"🔌 RabbitMQ connection closed: {exc}")
        self._is_connected = False

    async def _restore_consumers(self):
        """Восстановление consumers после переподключения"""
        if not self._consumers_to_restore:
            return

        logger.info(f"Restoring {len(self._consumers_to_restore)} consumers...")
        for queue_name, callback in self._consumers_to_restore.items():
            try:
                asyncio.create_task(self.consume(queue_name, callback))
            except Exception as e:
                logger.error(f"Failed to restore consumer for {queue_name}: {e}")

    async def _setup_queues_and_exchanges(self):
        """Настройка очередей и обменников"""
        logger.info("Setting up queues and exchanges...")

        main_exchange = await self.channel.declare_exchange(
            settings.exchange_main,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        dlx_exchange = await self.channel.declare_exchange(
            settings.exchange_dlx,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        # 1. Очередь приема результатов
        incoming_queue = await self.channel.declare_queue(
            settings.queue_incoming,
            durable=True,
            arguments={'x-queue-type': 'quorum'}
        )
        await incoming_queue.bind(main_exchange, 'lab.results.raw')

        # 2. Telegram
        telegram_queue = await self.channel.declare_queue(
            settings.queue_telegram,
            durable=True,
            arguments={
                'x-queue-type': 'classic',
                'x-message-ttl': settings.message_ttl,
                'x-dead-letter-exchange': settings.exchange_dlx,
                'x-dead-letter-routing-key': 'retry.telegram',
            }
        )
        await telegram_queue.bind(main_exchange, 'alert.telegram')

        # 3. App
        app_queue = await self.channel.declare_queue(
            settings.queue_app,
            durable=True,
            arguments={
                'x-queue-type': 'classic',
                'x-message-ttl': settings.message_ttl,
                'x-dead-letter-exchange': settings.exchange_dlx,
                'x-dead-letter-routing-key': 'retry.app',
            }
        )
        await app_queue.bind(main_exchange, 'alert.app')

        # 4. Pending
        pending_queue = await self.channel.declare_queue(
            settings.queue_pending,
            durable=True,
            arguments={'x-queue-type': 'quorum', 'x-delivery-limit': 10}
        )
        await pending_queue.bind(main_exchange, 'pending.confirmation')

        # 5. Response
        response_queue = await self.channel.declare_queue(
            settings.queue_response,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await response_queue.bind(main_exchange, 'response.processed')

        # 6. Rejected
        rejected_queue = await self.channel.declare_queue(
            settings.queue_rejected,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await rejected_queue.bind(main_exchange, 'result.rejected')

        # 7. Desktop confirmation
        desktop_queue = await self.channel.declare_queue(
            settings.queue_desktop_confirmation,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await desktop_queue.bind(main_exchange, 'desktop.confirmation')

        # 8. Retry
        retry_queue = await self.channel.declare_queue(
            settings.queue_retry_delay,
            durable=True,
            arguments={
                'x-queue-type': 'classic',
                'x-message-ttl': settings.retry_delay,
                'x-dead-letter-exchange': settings.exchange_main,
                'x-dead-letter-routing-key': 'alert.telegram',
            }
        )
        await retry_queue.bind(dlx_exchange, 'retry.telegram')
        await retry_queue.bind(dlx_exchange, 'retry.app')

        # 9. Failed
        failed_queue = await self.channel.declare_queue(
            settings.queue_failed,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await failed_queue.bind(dlx_exchange, 'failed.telegram')
        await failed_queue.bind(dlx_exchange, 'failed.app')

        logger.info("✅ All queues and exchanges configured")

    async def publish(
            self,
            routing_key: str,
            message: Dict[str, Any],
            exchange: str = None,
            priority: int = 0
    ) -> bool:
        """Публикация сообщения"""
        if not self._is_connected or not self.channel or self.channel.is_closed:
            logger.error(f"Cannot publish to {routing_key}: not connected")
            return False

        try:
            exchange_name = exchange or settings.exchange_main
            exchange_obj = await self.channel.get_exchange(exchange_name)

            message_body = json.dumps(message, default=str).encode()

            await exchange_obj.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    priority=priority,
                    content_type='application/json',
                    timestamp=datetime.utcnow(),
                ),
                routing_key=routing_key
            )

            logger.debug(f"Published to {routing_key}")
            return True

        except Exception as e:
            logger.error(f"Error publishing to {routing_key}: {e}")
            return False

    async def consume(
            self,
            queue_name: str,
            callback: Callable[[Dict[str, Any], Any], Awaitable[None]]
    ):
        """
        Подписка на очередь.

        ВАЖНО: callback НЕ должен вызывать message.ack() или message.nack() —
        это делается автоматически через message.process().
        """
        if not self._is_connected or not self.channel:
            logger.error(f"Cannot consume {queue_name}: not connected")
            return

        self._consumers_to_restore[queue_name] = callback

        while self._is_connected:
            try:
                queue = await self.channel.get_queue(queue_name)

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        try:
                            # process() САМ делает ack при успехе / nack при исключении
                            async with message.process(requeue=False, reject_on_redelivered=False):
                                body = json.loads(message.body.decode())
                                logger.debug(f"Received from {queue_name}")
                                await callback(body, message)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in {queue_name}: {e}")
                            # process() сделает nack автоматически
                        except Exception as e:
                            logger.error(f"Error processing from {queue_name}: {e}")
                            # process() сделает nack автоматически
                        # НЕ пытаемся делать ack/nack повторно!

            except asyncio.CancelledError:
                logger.info(f"Consumer for {queue_name} cancelled")
                raise
            except Exception as e:
                logger.error(f"Consumer for {queue_name} crashed: {e}")
                if self._is_connected:
                    await asyncio.sleep(5)
                else:
                    break

    async def health_check(self) -> bool:
        """Проверка реального состояния соединения"""
        if not self._is_connected:
            return False

        if not self.connection or self.connection.is_closed:
            self._is_connected = False
            return False

        if not self.channel or self.channel.is_closed:
            self._is_connected = False
            return False

        # Реальная проверка через ping
        try:
            # Открываем временный канал для проверки
            test_channel = await self.connection.channel()
            await test_channel.close()
            return True
        except Exception as e:
            logger.warning(f"RabbitMQ health check failed: {e}")
            self._is_connected = False
            return False

    def is_connected(self) -> bool:
        """Быстрая проверка (без сети)"""
        if not self._is_connected:
            return False
        if not self.connection or self.connection.is_closed:
            return False
        if not self.channel or self.channel.is_closed:
            return False
        return True

    async def ensure_connected(self, max_wait: int = 30) -> bool:
        """
        Гарантирует подключение. Если не подключено — пытается переподключиться.
        Возвращает True если удалось подключиться.
        """
        if self.is_connected():
            return True

        logger.warning("RabbitMQ not connected, attempting to reconnect...")

        for attempt in range(max_wait // 5):
            success = await self.connect()
            if success:
                return True
            logger.warning(f"Reconnect attempt {attempt + 1} failed, retrying in 5s...")
            await asyncio.sleep(5)

        return False

    async def close(self):
        """Закрытие соединения"""
        self._is_connected = False
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
        logger.info("RabbitMQ connection closed")


# Глобальный экземпляр
rabbitmq_client = RabbitMQClient()
