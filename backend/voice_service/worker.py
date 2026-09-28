# voice_service/worker.py
"""
Worker — сердце voice-сервиса.

Слушает voice.calls.queue и совершает звонки через Twilio.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal, VoiceCall, DepartmentPhone, init_db
from rabbitmq_client import rabbitmq_client
from twilio_client import twilio_client
from call_state import (
    acquire_call_lock,
    release_call_lock,
    is_result_confirmed,
    get_last_call,
)
from phrases import get_phrase
from tts import generate_audio, get_audio_url

logger = logging.getLogger(__name__)


class VoiceWorker:
    """Worker для обработки звонков."""

    def __init__(self):
        self.running = True

    async def start(self):
        logger.info("=" * 60)
        logger.info("VOICE WORKER ЗАПУЩЕН")
        logger.info(f"Twilio: {'настроен' if settings.is_twilio_configured() else 'НЕ НАСТРОЕН'}")
        logger.info(f"TTS: {settings.tts_provider}")
        logger.info(f"RabbitMQ: {settings.rabbitmq_host}:{settings.rabbitmq_port}")
        logger.info("=" * 60)

        init_db()

        if not await rabbitmq_client.connect():
            logger.error("Не удалось подключиться к RabbitMQ")
            return

        asyncio.create_task(
            rabbitmq_client.consume(
                settings.queue_voice_calls,
                self.handle_voice_call,
            )
        )
        logger.info(f"Consumer запущен на очереди {settings.queue_voice_calls}")

        while self.running:
            await asyncio.sleep(1)

    async def handle_voice_call(self, body: Dict[str, Any], message):
        """Обработка одного сообщения о звонке."""
        result_key = body.get('result_key')
        department = body.get('department', 'Неизвестное отделение')

        logger.info(f"📞 Обработка звонка для {result_key} ({department})")

        try:
            # 1. Проверяем, не подтверждён ли уже результат
            if is_result_confirmed(result_key):
                logger.info(f"⏭ {result_key} уже подтверждён, пропускаем")
                return

            # 2. Захватываем lock
            if not acquire_call_lock(result_key, ttl_minutes=60):
                logger.warning(f"⚠️ Lock уже взят для {result_key}, пропускаем")
                return

            # 3. Проверяем тихие часы
            if settings.is_quiet_hours_now() and not body.get('urgent'):
                logger.info(f"🌙 Тихие часы, пропускаем {result_key}")
                release_call_lock(result_key)
                return

            # 4. Ищем телефон
            phone = self._get_department_phone(department, role='duty')
            if not phone:
                logger.error(f"❌ Нет телефона для {department}")
                release_call_lock(result_key)
                await self._publish_failed(body, reason='no_phone')
                return

            # 5. Выбираем фразу
            phrase_key = self._choose_phrase(department)
            phrase_text = get_phrase(phrase_key)

            # 6. Генерируем аудио (если Yandex TTS)
            phrase_audio_url = None
            if settings.tts_provider == 'yandex':
                await generate_audio(phrase_text)
                phrase_audio_url = get_audio_url(phrase_text)

            # 7. Сохраняем запись о звонке ДО самого звонка (чтобы lock сработал)
            call_id = self._create_call_record(
                result_key=result_key,
                department=department,
                phone=phone,
                test_name=body.get('test_name'),
                result_value=body.get('result_value'),
                phrase_key=phrase_key,
            )

            # 8. Делаем звонок
            twilio_sid = twilio_client.make_call(
                to=phone,
                phrase_text=phrase_text,
                phrase_audio_url=phrase_audio_url,
            )

            if not twilio_sid:
                logger.error(f"❌ Не удалось создать звонок для {result_key}")
                self._update_call_record(call_id, status='failed', error_message='Twilio error')
                release_call_lock(result_key)
                await self._publish_failed(body, reason='twilio_error')
                return

            # 9. Обновляем запись с SID
            self._update_call_record(call_id, twilio_sid=twilio_sid, status='initiated')
            logger.info(f"✅ Звонок создан: {twilio_sid} для {result_key}")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки звонка: {e}", exc_info=True)
            raise

    # ==================== ХЕЛПЕРЫ ====================

    def _get_department_phone(self, department: str, role: str = 'duty') -> Optional[str]:
        """Получить телефон отделения."""
        db = SessionLocal()
        try:
            phone_record = db.query(DepartmentPhone).filter(
                DepartmentPhone.department == department,
                DepartmentPhone.role == role,
                DepartmentPhone.is_active == True,
            ).first()

            return phone_record.phone if phone_record else None
        finally:
            db.close()

    def _choose_phrase(self, department: str) -> str:
        """Выбрать фразу по отделению."""
        if 'Реанимационное' in department:
            return 'critical_reanimation'
        return 'critical_department'

    def _create_call_record(
        self,
        result_key: str,
        department: str,
        phone: str,
        test_name: Optional[str],
        result_value: Optional[float],
        phrase_key: str,
    ) -> int:
        """Создать запись о звонке в БД."""
        db = SessionLocal()
        try:
            call = VoiceCall(
                result_key=result_key,
                department=department,
                phone=phone,
                test_name=test_name,
                result_value=result_value,
                phrase_key=phrase_key,
                status='initiated',
                attempt=1,
            )
            db.add(call)
            db.commit()
            db.refresh(call)
            return call.id
        finally:
            db.close()

    def _update_call_record(self, call_id: int, **kwargs):
        """Обновить запись о звонке."""
        db = SessionLocal()
        try:
            call = db.query(VoiceCall).filter(VoiceCall.id == call_id).first()
            if not call:
                return

            for key, value in kwargs.items():
                if hasattr(call, key) and value is not None:
                    setattr(call, key, value)

            call.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления записи: {e}")
            db.rollback()
        finally:
            db.close()

    async def _publish_failed(self, body: Dict[str, Any], reason: str):
        """Опубликовать в failed-очередь."""
        try:
            payload = dict(body)
            payload['failure_reason'] = reason
            payload['failed_at'] = datetime.utcnow().isoformat()

            await rabbitmq_client.publish(
                settings.routing_voice_failed,
                payload,
                exchange=settings.exchange_dlx,
            )
            logger.warning(f"⚠️ Опубликован failed: {reason}")
        except Exception as e:
            logger.error(f"Ошибка публикации failed: {e}")


async def run_worker():
    """Точка входа для worker'а."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    worker = VoiceWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Worker остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        worker.running = False
        await rabbitmq_client.close()


if __name__ == "__main__":
    asyncio.run(run_worker())