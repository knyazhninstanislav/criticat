# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import logging
import sqlite3

from config import settings

logger = logging.getLogger(__name__)

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
    status = Column(String, default='pending')  # pending, sent, confirmed, rejected, expired
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    push_message_id = Column(String, nullable=True)
    mobile_user_id = Column(String, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)
    attempts_count = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_status_acknowledged', 'status', 'acknowledged'),
        Index('idx_created_at', 'created_at'),
    )


class MobileUser(Base):
    """Пользователь мобильного приложения / веба"""
    __tablename__ = "mobile_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    role = Column(String, default='doctor')  # doctor/admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_notification_at = Column(DateTime, nullable=True)


class UserSession(Base):
    """Сессия пользователя (refresh-токены)"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    access_jti = Column(String, unique=True, index=True, nullable=False)
    refresh_token_hash = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False, index=True)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    __table_args__ = (
        Index('idx_session_user_revoked', 'user_id', 'is_revoked'),
        # ← НОВОЕ: индекс для cleanup и reuse detection
        Index('idx_session_revoked_at', 'is_revoked', 'revoked_at'),
        Index('idx_session_expires_at', 'expires_at'),
    )


class NotificationLog(Base):
    """Лог уведомлений"""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, nullable=True)
    result_key = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    action = Column(String)  # sent, confirmed, rejected, expired, failed
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_result_key_action', 'result_key', 'action'),
    )


def get_db_path() -> str:
    if settings.database_url.startswith('sqlite:///'):
        return settings.database_url.replace('sqlite:///', '')
    return ''


def ensure_db_directory():
    db_path = get_db_path()
    if db_path:
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            os.chmod(db_dir, 0o777)
            logger.info(f"Директория БД: {db_dir}")


def ensure_db_writable():
    db_path = get_db_path()
    if db_path and os.path.exists(db_path):
        try:
            os.chmod(db_path, 0o666)
        except Exception as e:
            logger.warning(f"Не удалось изменить права: {e}")


def migrate_database():
    """Миграция БД"""
    db_path = get_db_path()
    if not db_path or not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # mobile_users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mobile_users'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(mobile_users)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'password_hash' not in columns:
                cursor.execute("ALTER TABLE mobile_users ADD COLUMN password_hash TEXT")
                logger.info("Добавлена колонка password_hash в mobile_users")

            if 'role' not in columns:
                cursor.execute("ALTER TABLE mobile_users ADD COLUMN role TEXT DEFAULT 'doctor'")
                logger.info("Добавлена колонка role в mobile_users")

        # anonymized_results
        cursor.execute("PRAGMA table_info(anonymized_results)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'rejection_reason' not in columns:
            cursor.execute("ALTER TABLE anonymized_results ADD COLUMN rejection_reason TEXT")

        if 'attempts_count' not in columns:
            cursor.execute("ALTER TABLE anonymized_results ADD COLUMN attempts_count INTEGER DEFAULT 0")

        # user_sessions
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(user_sessions)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'revoked_at' not in columns:
                cursor.execute("ALTER TABLE user_sessions ADD COLUMN revoked_at DATETIME")
                logger.info("Добавлена колонка revoked_at в user_sessions")

            if 'is_revoked' not in columns:
                cursor.execute("ALTER TABLE user_sessions ADD COLUMN is_revoked INTEGER DEFAULT 0")
                logger.info("Добавлена колонка is_revoked в user_sessions")

        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка миграции: {e}")


ensure_db_directory()
ensure_db_writable()

if settings.database_url.startswith('sqlite'):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
        echo=False,
    )
else:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    logger.info("Инициализация базы данных...")
    ensure_db_directory()
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы созданы")
    migrate_database()
    ensure_db_writable()

    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Существующие таблицы: {tables}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    return SessionLocal()


def close_db_session(db):
    if db:
        db.close()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_result_by_key(db, result_key: str):
    return db.query(AnonymizedResult).filter(
        AnonymizedResult.result_key == result_key
    ).first()


def get_result_by_id(db, result_id: int):
    return db.query(AnonymizedResult).filter(
        AnonymizedResult.id == result_id
    ).first()


def update_result_status(db, result_key: str, status: str):
    result = get_result_by_key(db, result_key)
    if result:
        result.status = status
        result.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


def mark_as_confirmed(db, result_key: str, user_id: str):
    result = get_result_by_key(db, result_key)
    if result:
        result.status = 'confirmed'
        result.confirmed_at = datetime.utcnow()
        result.confirmed_by = user_id
        result.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


def mark_as_rejected(db, result_key: str, user_id: str, reason: str = None):
    result = get_result_by_key(db, result_key)
    if result:
        result.status = 'rejected'
        result.confirmed_at = datetime.utcnow()
        result.confirmed_by = user_id
        result.rejection_reason = reason
        result.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


def mark_as_acknowledged(db, result_key: str):
    result = get_result_by_key(db, result_key)
    if result:
        result.acknowledged = True
        result.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


def delete_result(db, result_key: str) -> bool:
    try:
        db.query(NotificationLog).filter(
            NotificationLog.result_key == result_key
        ).delete()

        result = get_result_by_key(db, result_key)
        if result:
            db.delete(result)
            db.commit()
            logger.info(f"Результат удален: {result_key}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка удаления: {e}")
        return False


def get_pending_results(db) -> list:
    return db.query(AnonymizedResult).filter(
        AnonymizedResult.status == 'pending'
    ).all()


def get_sent_results(db) -> list:
    return db.query(AnonymizedResult).filter(
        AnonymizedResult.status == 'sent'
    ).all()


def get_confirmed_results(db) -> list:
    return db.query(AnonymizedResult).filter(
        AnonymizedResult.status == 'confirmed',
        AnonymizedResult.acknowledged == False
    ).all()


def get_all_results(db) -> list:
    return db.query(AnonymizedResult).order_by(
        AnonymizedResult.created_at.desc()
    ).all()


def get_active_users(db) -> list:
    return db.query(MobileUser).filter(
        MobileUser.is_active == True
    ).all()


def add_user(db, user_id: str, username: str = '', full_name: str = '', department: str = ''):
    user = MobileUser(
        user_id=user_id,
        username=username,
        full_name=full_name,
        department=department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db, user_id: str) -> bool:
    user = db.query(MobileUser).filter(MobileUser.user_id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
        return True
    return False


def add_notification_log(db, result_id: int, result_key: str, user_id: str,
                         message_id: str, action: str, details: str = None):
    log = NotificationLog(
        result_id=result_id,
        result_key=result_key,
        user_id=user_id,
        message_id=message_id,
        action=action,
        details=details,
    )
    db.add(log)
    db.commit()
    return log


def get_statistics(db) -> dict:
    total = db.query(AnonymizedResult).count()
    pending = db.query(AnonymizedResult).filter(AnonymizedResult.status == 'pending').count()
    sent = db.query(AnonymizedResult).filter(AnonymizedResult.status == 'sent').count()
    confirmed = db.query(AnonymizedResult).filter(AnonymizedResult.status == 'confirmed').count()
    rejected = db.query(AnonymizedResult).filter(AnonymizedResult.status == 'rejected').count()
    expired = db.query(AnonymizedResult).filter(AnonymizedResult.status == 'expired').count()
    acknowledged = db.query(AnonymizedResult).filter(AnonymizedResult.acknowledged == True).count()

    return {
        'total': total,
        'pending': pending,
        'sent': sent,
        'confirmed': confirmed,
        'rejected': rejected,
        'expired': expired,
        'acknowledged': acknowledged,
    }


def cleanup_old_results(db, days: int = 7) -> int:
    cutoff = datetime.utcnow() - timedelta(days=days)
    old_results = db.query(AnonymizedResult).filter(
        AnonymizedResult.created_at < cutoff,
        AnonymizedResult.status.in_(['confirmed', 'rejected', 'expired'])
    ).all()

    deleted = 0
    for result in old_results:
        if delete_result(db, result.result_key):
            deleted += 1
    return deleted