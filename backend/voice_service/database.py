# voice_service/database.py
"""
БД voice-сервиса.

Здесь только логи звонков и телефоны отделений.
Основную БД CritiCat не трогаем.
"""
import os
import logging
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class VoiceCall(Base):
    """Один звонок робота."""
    __tablename__ = "voice_calls"

    id = Column(Integer, primary_key=True, index=True)
    result_key = Column(String, index=True, nullable=False)
    twilio_sid = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=False)
    department = Column(String, nullable=True)
    test_name = Column(String, nullable=True)
    result_value = Column(Float, nullable=True)
    phrase_key = Column(String, nullable=True)

    status = Column(String, default='initiated', index=True)
    # initiated, ringing, in-progress, completed, busy, failed, no-answer, canceled

    duration_seconds = Column(Integer, nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    attempt = Column(Integer, default=1)
    escalation_level = Column(String, default='duty')

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_result_key_status', 'result_key', 'status'),
    )


class DepartmentPhone(Base):
    """Телефоны отделений."""
    __tablename__ = "department_phones"

    id = Column(Integer, primary_key=True, index=True)
    department = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(String, default='duty')
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# === Создание движка ===

def _get_engine_url() -> str:
    url = settings.voice_db_url
    if url.startswith('sqlite:///'):
        path = url.replace('sqlite:///', '')
        db_dir = os.path.dirname(path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    return url


engine = create_engine(
    _get_engine_url(),
    connect_args={"check_same_thread": False} if settings.voice_db_url.startswith('sqlite') else {},
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Создать таблицы."""
    logger.info("Инициализация БД voice-сервиса...")
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы voice-сервиса созданы")
    _seed_default_phones()


def _seed_default_phones():
    """Заглушка: телефоны отделений по умолчанию."""
    db = SessionLocal()
    try:
        existing = db.query(DepartmentPhone).count()
        if existing > 0:
            return

        default_phones = [
            ('Терапевтическое отделение', '+79000000001', 'duty'),
            ('Хирургическое отделение', '+79000000002', 'duty'),
            ('Кардиологическое отделение', '+79000000003', 'duty'),
            ('Неврологическое отделение', '+79000000004', 'duty'),
            ('Реанимационное отделение', '+79000000005', 'duty'),
        ]

        for dept, phone, role in default_phones:
            db.add(DepartmentPhone(department=dept, phone=phone, role=role))

        db.commit()
        logger.info(f"Засеяно {len(default_phones)} телефонов отделений")
    except Exception as e:
        logger.error(f"Ошибка seed: {e}")
        db.rollback()
    finally:
        db.close()


def get_db_session():
    return SessionLocal()