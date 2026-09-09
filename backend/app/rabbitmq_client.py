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
        
        # Создаем основной обменник (EXCHANGE, а не очередь!)
        main_exchange = await self.channel.declare_exchange(
            settings.exchange_main,  # 'lab.exchange'
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        logger.info(f"Exchange '{settings.exchange_main}' created")
        
        # Создаем DLX обменник
        dlx_exchange = await self.channel.declare_exchange(
            settings.exchange_dlx,  # 'lab.dlx.exchange'
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        logger.info(f"Exchange '{settings.exchange_dlx}' created")
        
        # 1. Очередь приема результатов (от десктопа)
        incoming_queue = await self.channel.declare_queue(
            settings.queue_incoming,  # 'lab.critical.results' - это ОЧЕРЕДЬ
            durable=True,
            arguments={
                'x-queue-type': 'quorum',
            }
        )
        # Привязываем очередь к exchange
        await incoming_queue.bind(main_exchange, 'lab.results.raw')
        logger.info(f"Queue '{settings.queue_incoming}' created and bound")
        
        # 2. Очередь для Telegram
        telegram_queue = await self.channel.declare_queue(
            settings.queue_telegram,  # 'alert.telegram.queue'
            durable=True,
            arguments={
                'x-queue-type': 'classic',
                'x-message-ttl': settings.message_ttl,
                'x-dead-letter-exchange': settings.exchange_dlx,
                'x-dead-letter-routing-key': 'retry.telegram',
            }
        )
        await telegram_queue.bind(main_exchange, 'alert.telegram')
        logger.info(f"Queue '{settings.queue_telegram}' created and bound")
        
        # 3. Очередь для App
        app_queue = await self.channel.declare_queue(
            settings.queue_app,  # 'alert.app.queue'
            durable=True,
            arguments={
                'x-queue-type': 'classic',
                'x-message-ttl': settings.message_ttl,
                'x-dead-letter-exchange': settings.exchange_dlx,
                'x-dead-letter-routing-key': 'retry.app',
            }
        )
        await app_queue.bind(main_exchange, 'alert.app')
        logger.info(f"Queue '{settings.queue_app}' created and bound")
        
        # 4. Очередь ожидания подтверждения (Quorum Queue)
        pending_queue = await self.channel.declare_queue(
            settings.queue_pending,  # 'pending.confirmation.queue'
            durable=True,
            arguments={
                'x-queue-type': 'quorum',
                'x-delivery-limit': 10,
            }
        )
        await pending_queue.bind(main_exchange, 'pending.confirmation')
        logger.info(f"Queue '{settings.queue_pending}' created and bound")
        
        # 5. Очередь ответов пользователей
        response_queue = await self.channel.declare_queue(
            settings.queue_response,  # 'user.response.queue'
            durable=True,
            arguments={
                'x-queue-type': 'classic',
            }
        )
        await response_queue.bind(main_exchange, 'response.processed')
        logger.info(f"Queue '{settings.queue_response}' created and bound")
        
        # 6. Очередь отклоненных результатов
        rejected_queue = await self.channel.declare_queue(
            settings.queue_rejected,  # 'rejected.results.queue'
            durable=True,
            arguments={
                'x-queue-type': 'classic',
            }
        )
        await rejected_queue.bind(main_exchange, 'result.rejected')
        logger.info(f"Queue '{settings.queue_rejected}' created and bound")
        
        # 7. Очередь подтверждений для десктопа
        desktop_queue = await self.channel.declare_queue(
            settings.queue_desktop_confirmation,  # 'desktop.confirmation.queue'
            durable=True,
            arguments={
                'x-queue-type': 'classic',
            }
        )
        await desktop_queue.bind(main_exchange, 'desktop.confirmation')
        logger.info(f"Queue '{settings.queue_desktop_confirmation}' created and bound")
        
        # 8. Очередь задержки для retry
        retry_queue = await self.channel.declare_queue(
            settings.queue_retry_delay,  # 'retry.delay.queue'
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
        logger.info(f"Queue '{settings.queue_retry_delay}' created and bound")
        
        # 9. Очередь failed сообщений
        failed_queue = await self.channel.declare_queue(
            settings.queue_failed,  # 'failed.alerts.queue'
            durable=True,
            arguments={
                'x-queue-type': 'classic',
            }
        )
        await failed_queue.bind(dlx_exchange, 'failed.telegram')
        await failed_queue.bind(dlx_exchange, 'failed.app')
        logger.info(f"Queue '{settings.queue_failed}' created and bound")
        
        logger.info("All queues and exchanges configured successfully")

    async def publish(self, routing_key: str, message: Dict[str, Any], 
                     exchange: str = None, priority: int = 0) -> bool:
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
            
            logger.debug(f"Published to {routing_key}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing to {routing_key}: {e}")
            return False
    
    async def consume(self, queue_name: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        """Подписка на очередь"""
        if not self._is_connected or not self.channel:
            logger.error("Cannot consume: not connected")
            return
        
        try:
            queue = await self.channel.get_queue(queue_name)
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process(requeue=False):
                        try:
                            body = json.loads(message.body.decode())
                            logger.debug(f"Received from {queue_name}: {body}")
                            
                            await callback(body, message)
                            
                            await message.ack()
                            
                        except Exception as e:
                            logger.error(f"Error processing message from {queue_name}: {e}")
                            await message.nack(requeue=True)
                            
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