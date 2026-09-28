# voice_service/call_state.py
"""
Состояние звонков через БД (без Redis).

Здесь:
- lock на звонок по result_key (защита от двойного)
- проверка, подтверждён ли результат
- обновление статуса звонка
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_

from database import SessionLocal, VoiceCall

logger = logging.getLogger(__name__)

# Статусы, которые считаются "звонок ещё идёт или только что был"
ACTIVE_STATUSES = ('initiated', 'ringing', 'in-progress')


def acquire_call_lock(result_key: str, ttl_minutes: int = 60) -> bool:
    """
    Попытаться захватить lock на звонок по result_key.

    Возвращает True, если можно звонить.
    False, если по этому result_key уже был звонок за последние ttl_minutes.

    Lock — это запись в voice_calls с активным статусом.
    """
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=ttl_minutes)

        existing = db.query(VoiceCall).filter(
            and_(
                VoiceCall.result_key == result_key,
                VoiceCall.created_at >= cutoff,
            )
        ).first()

        if existing:
            logger.info(
                f"Lock уже взят для {result_key} "
                f"(status={existing.status}, sid={existing.twilio_sid})"
            )
            return False

        return True
    finally:
        db.close()


def release_call_lock(result_key: str):
    """
    Снять lock — пометить последний звонок как failed/canceled,
    чтобы не блокировать повторные попытки.
    """
    db = SessionLocal()
    try:
        last = db.query(VoiceCall).filter(
            VoiceCall.result_key == result_key,
        ).order_by(VoiceCall.created_at.desc()).first()

        if last and last.status in ACTIVE_STATUSES:
            last.status = 'canceled'
            last.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Lock снят для {result_key}")
    except Exception as e:
        logger.error(f"Ошибка снятия lock: {e}")
        db.rollback()
    finally:
        db.close()


def mark_result_confirmed(result_key: str):
    """
    Пометить результат как подтверждённый.

    Создаём фиктивную запись VoiceCall со статусом 'completed',
    чтобы проверка is_result_confirmed сработала.
    """
    db = SessionLocal()
    try:
        # Если уже есть completed — не дублируем
        existing = db.query(VoiceCall).filter(
            VoiceCall.result_key == result_key,
            VoiceCall.status == 'completed',
        ).first()

        if existing:
            return

        call = VoiceCall(
            result_key=result_key,
            phone='',
            status='completed',
            phrase_key='manual_confirm',
            attempt=0,
            escalation_level='manual',
        )
        db.add(call)
        db.commit()
        logger.info(f"Результат {result_key} помечен как подтверждённый")
    except Exception as e:
        logger.error(f"Ошибка пометки confirmed: {e}")
        db.rollback()
    finally:
        db.close()


def is_result_confirmed(result_key: str) -> bool:
    """
    Проверить, подтверждён ли результат.

    Считаем подтверждённым, если есть VoiceCall со статусом 'completed'
    или 'answered' (трубку взяли).
    """
    db = SessionLocal()
    try:
        confirmed = db.query(VoiceCall).filter(
            VoiceCall.result_key == result_key,
            VoiceCall.status.in_(('completed', 'answered')),
        ).first()

        return confirmed is not None
    finally:
        db.close()


def get_last_call(result_key: str) -> Optional[VoiceCall]:
    """Получить последний звонок по result_key."""
    db = SessionLocal()
    try:
        return db.query(VoiceCall).filter(
            VoiceCall.result_key == result_key,
        ).order_by(VoiceCall.created_at.desc()).first()
    finally:
        db.close()


def get_call_by_sid(twilio_sid: str) -> Optional[VoiceCall]:
    """Получить звонок по Twilio SID."""
    db = SessionLocal()
    try:
        return db.query(VoiceCall).filter(
            VoiceCall.twilio_sid == twilio_sid,
        ).first()
    finally:
        db.close()


def update_call_status(twilio_sid: str, status: str, **kwargs):
    """
    Обновить статус звонка по SID.
    Дополнительные поля (duration, error_code) — через kwargs.
    """
    db = SessionLocal()
    try:
        call = db.query(VoiceCall).filter(
            VoiceCall.twilio_sid == twilio_sid,
        ).first()

        if not call:
            logger.warning(f"Звонок с SID {twilio_sid} не найден")
            return

        call.status = status
        call.updated_at = datetime.utcnow()

        for key, value in kwargs.items():
            if hasattr(call, key) and value is not None:
                setattr(call, key, value)

        db.commit()
        logger.debug(f"Статус звонка {twilio_sid} → {status}")
    except Exception as e:
        logger.error(f"Ошибка обновления статуса: {e}")
        db.rollback()
    finally:
        db.close()