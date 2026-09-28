# voice_service/rabbitmq_client.py
"""
RabbitMQ-клиент voice-сервиса.
"""
import json
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

import aio_pika

from config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Клиент RabbitMQ для voice-сервиса."""

    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self._is_connected = False
        self._consumers_to_restore: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        async with self._lock:
            if self._is_connected and self.connection and not self.connection.is_closed:
                return True

            try:
                url = (
                    f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}@"
                    f"{settings.rabbitmq_host}:{settings.rabbitmq_port}/"
                    f"{settings.rabbitmq_vhost}"
                )

                logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_host}")

                self.connection = await aio_pika.connect_robust(
                    url,
                    reconnect_interval=5,
                    fail_fast=False,
                )

                self.connection.reconnect_callbacks.add(self._on_reconnect)
                self.connection.close_callbacks.add(self._on_close)

                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=1)

                await self._setup_queues()

                self._is_connected = True
                logger.info("✅ Voice-service подключён к RabbitMQ")

                await self._restore_consumers()
                return True

            except Exception as e:
                self._is_connected = False
                logger.error(f"❌ Ошибка подключения к RabbitMQ: {e}")
                return False

    def _on_reconnect(self, connection):
        logger.info("🔄 RabbitMQ переподключён")
        self._is_connected = True
        asyncio.create_task(self._restore_consumers())

    def _on_close(self, connection, exc):
        logger.warning(f"🔌 RabbitMQ закрыт: {exc}")
        self._is_connected = False

    async def _restore_consumers(self):
        if not self._consumers_to_restore:
            return
        logger.info(f"Восстанавливаем {len(self._consumers_to_restore)} consumer'ов")
        for queue_name, callback in self._consumers_to_restore.items():
            asyncio.create_task(self.consume(queue_name, callback))

    async def _setup_queues(self):
        """Voice-сервис подключается к уже созданным очередям."""
        logger.info("Проверка voice-очередей...")

        try:
            await self.channel.get_queue(settings.queue_voice_calls)
            logger.info(f"✅ Очередь {settings.queue_voice_calls} найдена")
        except Exception as e:
            logger.warning(f"Очередь {settings.queue_voice_calls} не найдена: {e}")
            main_exchange = await self.channel.get_exchange(settings.exchange_main)
            queue = await self.channel.declare_queue(
                settings.queue_voice_calls,
                durable=True,
                arguments={'x-queue-type': 'quorum'},
            )
            await queue.bind(main_exchange, settings.routing_voice_call)
            logger.info(f"Очередь {settings.queue_voice_calls} создана")

    async def publish(
        self,
        routing_key: str,
        message: Dict[str, Any],
        exchange: Optional[str] = None,
    ) -> bool:
        if not self.is_connected():
            logger.error(f"Нет соединения, не могу опубликовать в {routing_key}")
            return False

        try:
            exchange_name = exchange or settings.exchange_main
            exchange_obj = await self.channel.get_exchange(exchange_name)

            body = json.dumps(message, default=str).encode()

            await exchange_obj.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type='application/json',
                    timestamp=datetime.utcnow(),
                ),
                routing_key=routing_key,
            )
            return True

        except Exception as e:
            logger.error(f"Ошибка публикации в {routing_key}: {e}")
            return False

    async def consume(
        self,
        queue_name: str,
        callback: Callable[[Dict[str, Any], Any], Awaitable[None]],
    ):
        if not self.is_connected():
            logger.error(f"Нет соединения, не могу слушать {queue_name}")
            return

        self._consumers_to_restore[queue_name] = callback

        while self._is_connected:
            try:
                queue = await self.channel.get_queue(queue_name)

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        try:
                            async with message.process(
                                requeue=False,
                                reject_on_redelivered=False,
                            ):
                                body = json.loads(message.body.decode())
                                logger.debug(f"Получено из {queue_name}")
                                await callback(body, message)
                        except json.JSONDecodeError as e:
                            logger.error(f"Невалидный JSON в {queue_name}: {e}")
                        except Exception as e:
                            logger.error(f"Ошибка обработки из {queue_name}: {e}")

            except asyncio.CancelledError:
                logger.info(f"Consumer {queue_name} отменён")
                raise
            except Exception as e:
                logger.error(f"Consumer {queue_name} упал: {e}")
                if self._is_connected:
                    await asyncio.sleep(5)
                else:
                    break

    def is_connected(self) -> bool:
        if not self._is_connected:
            return False
        if not self.connection or self.connection.is_closed:
            return False
        if not self.channel or self.channel.is_closed:
            return False
        return True

    async def close(self):
        self._is_connected = False
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
            except Exception as e:
                logger.warning(f"Ошибка закрытия: {e}")
        logger.info("RabbitMQ voice-сервиса закрыт")




rabbitmq_client = RabbitMQClient()