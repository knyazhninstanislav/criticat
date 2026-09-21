# message_handlers.py
import logging
from datetime import datetime
from typing import Dict, Any

from .result_service import ResultService
from .config import settings
from .rabbitmq_client import rabbitmq_client

logger = logging.getLogger(__name__)


class MessageHandlers:
    """Обработчики сообщений из RabbitMQ (без Telegram)"""

    def __init__(self):
        self._sent_messages = set()

    async def handle_incoming_result(self, body: Dict[str, Any], message):
        """Обработка нового результата от десктопа"""
        try:
            service = ResultService()
            result = service.create_result(body)

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

            # Отправляем в очередь мобильного приложения
            await rabbitmq_client.publish('alert.app', result_data)

            # Отправляем в очередь ожидания подтверждения
            await rabbitmq_client.publish('pending.confirmation', result_data)

            service.close()
            logger.info(f"Result {result.result_key} routed to queues")

        except Exception as e:
            logger.error(f"Error handling incoming result: {e}")
            raise

    async def handle_alert_app(self, body: Dict[str, Any], message):
        """
        Обработка алерта для мобильного приложения.

        Логика:
        - Если нет активных получателей → failed, ACK
        - Если push-сервис недоступен (timeout) → НЕ ACK → retry
        - Если пользователь деактивирован → ACK
        - Если отправлено хотя бы одному → ACK
        """
        result_key = body.get('result_key')
        ids = body.get('ids')
        department = body.get('department')
        attempt = body.get('attempts', 0)

        logger.info(f"Processing alert for {result_key} (attempt {attempt + 1})")

        service = ResultService()
        try:
            users = service.get_active_users()

            if not users:
                logger.warning(f"No active users for {result_key}")
                await rabbitmq_client.publish('failed.app', body, settings.exchange_dlx)
                return

            sent_count = 0
            skipped_count = 0
            retry_needed = False

            for user in users:
                if not user.is_active:
                    skipped_count += 1
                    continue

                # TODO: здесь будет отправка push через FCM
                # Пока просто логируем
                try:
                    # Заглушка: push отправлен успешно
                    message_id = f"push-{result_key}-{user.user_id}"

                    sent_count += 1
                    service.mark_as_sent(
                        body.get('result_id'),
                        user.user_id,
                        message_id
                    )
                    logger.info(f"✅ Push sent to {user.user_id}: {result_key}")

                except Exception as e:
                    logger.error(f"Exception sending to {user.user_id}: {e}")
                    retry_needed = True

            logger.info(
                f"Alert {result_key}: sent={sent_count}, "
                f"skipped={skipped_count}, retry_needed={retry_needed}"
            )

            if sent_count > 0:
                logger.info(f"✅ Alert {result_key} delivered to {sent_count} users")
                return

            if retry_needed and attempt < settings.max_retries:
                logger.warning(f"⚠️ Retry needed for {result_key} (attempt {attempt + 1})")
                body['attempts'] = attempt + 1
                raise Exception(f"Push service unavailable, retry attempt {attempt + 1}")

            logger.error(f"❌ Failed to deliver {result_key} after {attempt + 1} attempts")
            await rabbitmq_client.publish('failed.app', body, settings.exchange_dlx)

        finally:
            service.close()

    async def handle_user_response(self, body: Dict[str, Any], message):
        """Обработка ответа от пользователя (из мобильного приложения)"""
        try:
            result_id = body.get('result_id')
            result_key = body.get('result_key')
            action = body.get('action')
            user_id = body.get('user_id')

            service = ResultService()

            if action == 'approved':
                service.mark_as_confirmed(result_id, user_id)

                confirmation_data = {
                    'result_id': result_id,
                    'result_key': result_key,
                    'action': 'approved',
                    'confirmed_by': user_id,
                    'confirmed_at': datetime.utcnow().isoformat()
                }
                await rabbitmq_client.publish('desktop.confirmation', confirmation_data)

                logger.info(f"Result {result_key} confirmed by {user_id}")

            elif action == 'rejected':
                reason = body.get('reason')
                service.mark_as_rejected(result_id, user_id, reason)

                rejected_data = {
                    'result_id': result_id,
                    'result_key': result_key,
                    'ids': body.get('ids'),
                    'department': body.get('department'),
                    'test_name': body.get('test_name'),
                    'result_value': body.get('result_value'),
                    'rejected_by': user_id,
                    'reason': reason,
                    'rejected_at': datetime.utcnow().isoformat()
                }
                await rabbitmq_client.publish('result.rejected', rejected_data)

                logger.info(f"Result {result_key} rejected by {user_id}")

            service.close()

        except Exception as e:
            logger.error(f"Error handling user response: {e}")
            raise

    async def handle_rejected_result(self, body: Dict[str, Any], message):
        """Обработка отклоненного результата"""
        try:
            service = ResultService()
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
            service.mark_as_expired(result_id)

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