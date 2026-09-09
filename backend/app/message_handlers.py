# message_handlers.py
import logging
import json
from datetime import datetime
from typing import Dict, Any
import asyncio

from .result_service import ResultService
from .telegram_bot import TelegramBot
from .config import settings
from .rabbitmq_client import rabbitmq_client

logger = logging.getLogger(__name__)


class MessageHandlers:
    """Обработчики сообщений из RabbitMQ"""

    def __init__(self, telegram_bot: TelegramBot):
        self.telegram_bot = telegram_bot
        self._sent_messages = set()

    async def handle_incoming_result(self, body: Dict[str, Any], message):
        """Обработка нового результата от десктопа"""
        try:
            service = ResultService()

            # Сохраняем результат в БД
            result = service.create_result(body)

            # Отправляем в очередь рассылки
            result_data = {
                'result_id': result.id,
                'result_key': result.result_key,
                'ids': result.ids,
                'department': result.department,
                'test_name': result.test_name,
                'result_value': result.result_value,
                'ref_lower': result.ref_lower,
                'ref_upper': result.ref_upper,
                'deviation_percent': result.deviation_percent,
                'monitor_type': result.monitor_type,
                'status': result.status,
                'created_at': result.created_at.isoformat(),
                'attempts': 0
            }

            # Отправляем в Telegram очередь
            await rabbitmq_client.publish('alert.telegram', result_data)

            # Отправляем в App очередь (если нужно)
            if result.monitor_type in ['both', 'app']:
                await rabbitmq_client.publish('alert.app', result_data)

            # Отправляем в очередь ожидания подтверждения
            await rabbitmq_client.publish('pending.confirmation', result_data)

            service.close()
            logger.info(f"Result {result.result_key} routed to queues")

        except Exception as e:
            logger.error(f"Error handling incoming result: {e}")
            raise

    async def handle_alert_telegram(self, body: Dict[str, Any], message):
        """Обработка алерта для Telegram"""
        try:
            result_id = body.get('result_id')
            result_key = body.get('result_key')
            ids = body.get('ids')
            department = body.get('department')

            # Получаем активных пользователей
            service = ResultService()
            users = service.get_active_users()

            if not users:
                logger.warning("No active Telegram users")
                # Отправляем в failed очередь
                await rabbitmq_client.publish(
                    'failed.telegram',
                    body,
                    settings.exchange_dlx
                )
                service.close()
                return

            # Отправляем уведомления всем пользователям
            sent_count = 0
            for user in users:
                try:
                    # Отправляем сообщение
                    message_id = await self.telegram_bot.send_notification(
                        chat_id=user.chat_id,
                        ids=ids,
                        department=department,
                        results=[body]  # Передаем как список для совместимости
                    )

                    if message_id:
                        sent_count += 1
                        # Отмечаем результат как отправленный
                        service.mark_as_sent(result_id, user.chat_id, message_id)
                        logger.info(f"Telegram sent to {user.chat_id}: {result_key}")
                    else:
                        logger.error(f"Failed to send to {user.chat_id}")

                except Exception as e:
                    logger.error(f"Error sending to {user.chat_id}: {e}")

            service.close()

            if sent_count == 0:
                # Если никому не отправили - в failed
                await rabbitmq_client.publish(
                    'failed.telegram',
                    body,
                    settings.exchange_dlx
                )

        except Exception as e:
            logger.error(f"Error handling alert telegram: {e}")
            raise

    async def handle_user_response(self, body: Dict[str, Any], message):
        """Обработка ответа от пользователя"""
        try:
            result_id = body.get('result_id')
            result_key = body.get('result_key')
            action = body.get('action')
            chat_id = body.get('chat_id')

            service = ResultService()

            if action == 'approved':
                # Подтверждаем результат
                service.mark_as_confirmed(result_id, chat_id)

                # Отправляем подтверждение на десктоп
                confirmation_data = {
                    'result_id': result_id,
                    'result_key': result_key,
                    'action': 'approved',
                    'confirmed_by': chat_id,
                    'confirmed_at': datetime.utcnow().isoformat()
                }
                await rabbitmq_client.publish('desktop.confirmation', confirmation_data)

                logger.info(f"Result {result_key} confirmed by {chat_id}")

            elif action == 'rejected':
                # Отклоняем результат
                reason = body.get('reason')
                service.mark_as_rejected(result_id, chat_id, reason)

                # Отправляем в очередь отклоненных
                rejected_data = {
                    'result_id': result_id,
                    'result_key': result_key,
                    'ids': body.get('ids'),
                    'department': body.get('department'),
                    'test_name': body.get('test_name'),
                    'result_value': body.get('result_value'),
                    'rejected_by': chat_id,
                    'reason': reason,
                    'rejected_at': datetime.utcnow().isoformat()
                }
                await rabbitmq_client.publish('result.rejected', rejected_data)

                logger.info(f"Result {result_key} rejected by {chat_id}")

            service.close()

        except Exception as e:
            logger.error(f"Error handling user response: {e}")
            raise

    async def handle_rejected_result(self, body: Dict[str, Any], message):
        """Обработка отклоненного результата - сохранение в БД"""
        try:
            service = ResultService()

            # Здесь можно сохранить отклоненный результат в отдельную таблицу
            # или просто отметить как обработанный

            # Отмечаем как обработанный десктопом
            service.mark_as_acknowledged(body.get('result_key'))

            service.close()
            logger.info(f"Rejected result {body.get('result_key')} processed")

        except Exception as e:
            logger.error(f"Error handling rejected result: {e}")
            raise

    async def handle_desktop_confirmation(self, body: Dict[str, Any], message):
        """Обработка подтверждения от десктопа"""
        try:
            service = ResultService()

            # Отмечаем результат как полученный десктопом
            service.mark_as_acknowledged(body.get('result_key'))

            service.close()
            logger.info(f"Desktop confirmed result {body.get('result_key')}")

        except Exception as e:
            logger.error(f"Error handling desktop confirmation: {e}")
            raise

    async def handle_pending_timeout(self, body: Dict[str, Any], message):
        """Обработка просроченных ожидающих результатов"""
        try:
            result_id = body.get('result_id')

            service = ResultService()

            # Отмечаем как просроченный
            service.mark_as_expired(result_id)

            # Отправляем в очередь отклоненных
            rejected_data = {
                'result_id': result_id,
                'result_key': body.get('result_key'),
                'reason': 'timeout - user did not respond',
                'rejected_at': datetime.utcnow().isoformat()
            }
            await rabbitmq_client.publish('result.rejected', rejected_data)

            service.close()
            logger.info(f"Result {body.get('result_key')} expired")

        except Exception as e:
            logger.error(f"Error handling pending timeout: {e}")
            raise