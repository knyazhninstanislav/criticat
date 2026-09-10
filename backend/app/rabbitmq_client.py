# app/rabbitmq_client.py
import aio_pika
import json
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Клиент для работы с RabbitMQ"""

    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self._consumers: Dict[str, Callable] = {}
        self._is_connected = False

    async def connect(self) -> bool:
        """Подключение к RabbitMQ"""
        try:
            url = f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}@" \
                  f"{settings.rabbitmq_host}:{settings.rabbitmq_port}/{settings.rabbitmq_vhost}"

            logger.info(f"Connecting to RabbitMQ at {settings.rabbitmq_host}:{settings.rabbitmq_port}")

            self.connection = await aio_pika.connect_robust(url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)

            await self._setup_queues_and_exchanges()

            self._is_connected = True
            logger.info("Connected to RabbitMQ successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

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

        # 1. Очередь приема результатов (Quorum)
        incoming_queue = await self.channel.declare_queue(
            settings.queue_incoming,
            durable=True,
            arguments={'x-queue-type': 'quorum'}
        )
        await incoming_queue.bind(main_exchange, 'lab.results.raw')

        # 2. Telegram очередь (Classic, TTL + DLX)
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

        # 3. App очередь
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

        # 4. Pending очередь (Quorum)
        pending_queue = await self.channel.declare_queue(
            settings.queue_pending,
            durable=True,
            arguments={
                'x-queue-type': 'quorum',
                'x-delivery-limit': 10,
            }
        )
        await pending_queue.bind(main_exchange, 'pending.confirmation')

        # 5. Ответы пользователей
        response_queue = await self.channel.declare_queue(
            settings.queue_response,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await response_queue.bind(main_exchange, 'response.processed')

        # 6. Отклоненные
        rejected_queue = await self.channel.declare_queue(
            settings.queue_rejected,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await rejected_queue.bind(main_exchange, 'result.rejected')

        # 7. Подтверждения десктопу
        desktop_queue = await self.channel.declare_queue(
            settings.queue_desktop_confirmation,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await desktop_queue.bind(main_exchange, 'desktop.confirmation')

        # 8. Retry очередь
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

        # 9. Failed очередь
        failed_queue = await self.channel.declare_queue(
            settings.queue_failed,
            durable=True,
            arguments={'x-queue-type': 'classic'}
        )
        await failed_queue.bind(dlx_exchange, 'failed.telegram')
        await failed_queue.bind(dlx_exchange, 'failed.app')

        logger.info("All queues and exchanges configured successfully")

    async def publish(
            self,
            routing_key: str,
            message: Dict[str, Any],
            exchange: str = None,
            priority: int = 0
    ) -> bool:
        """Публикация сообщения"""
        if not self._is_connected or not self.channel:
            logger.error("Cannot publish: not connected")
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

        Если callback завершился без исключения — сообщение подтверждается (ack).
        Если callback бросил исключение — сообщение отклоняется (nack с requeue=False).
        """
        if not self._is_connected or not self.channel:
            logger.error("Cannot consume: not connected")
            return

        try:
            queue = await self.channel.get_queue(queue_name)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    # process() автоматически делает ack/nack
                    # requeue=False — не возвращаем в очередь при ошибке
                    async with message.process(requeue=False):
                        try:
                            body = json.loads(message.body.decode())
                            logger.debug(f"Received from {queue_name}: {body}")

                            # Callback НЕ должен делать ack/nack
                            await callback(body, message)

                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in {queue_name}: {e}")
                            # Сообщение будет nack'нуто автоматически
                            raise
                        except Exception as e:
                            logger.error(f"Error processing message from {queue_name}: {e}")
                            # Сообщение будет nack'нуто (requeue=False → DLX)
                            raise

        except Exception as e:
            logger.error(f"Error consuming from {queue_name}: {e}")

    async def close(self):
        """Закрытие соединения"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self._is_connected = False
            logger.info("RabbitMQ connection closed")

    def is_connected(self) -> bool:
        return self._is_connected


# Глобальный экземпляр
rabbitmq_client = RabbitMQClient()