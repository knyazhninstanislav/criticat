from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

from .config import settings

Base = declarative_base()

class AnonymizedResult(Base):
    """Обезличенный результат"""
    __tablename__ = "anonymized_results"
    
    id = Column(Integer, primary_key=True, index=True)
    result_key = Column(String, unique=True, index=True)
    ids = Column(Integer, index=True)
    department = Column(String)
    test_name = Column(String)
    result_value = Column(Float)
    ref_lower = Column(Float, nullable=True)
    ref_upper = Column(Float, nullable=True)
    deviation_percent = Column(Float, nullable=True)
    monitor_type = Column(String, default='both')
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    telegram_message_id = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(String, nullable=True)

class TelegramUser(Base):
    """Пользователь Telegram"""
    __tablename__ = "telegram_users"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, unique=True, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class NotificationLog(Base):
    """Лог уведомлений"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, nullable=True)
    result_key = Column(String, nullable=True)
    chat_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    action = Column(String)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Создание директории для SQLite
if settings.database_url.startswith('sqlite:///'):
    db_path = settings.database_url.replace('sqlite:///', '')
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

# Создание engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Получение сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()