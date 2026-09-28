# app/auth/service.py
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from ..config import settings
from ..database import MobileUser, UserSession, get_db_session
from .jwt_utils import create_access_token
from .password import verify_password, hash_password

logger = logging.getLogger(__name__)


def _hash_refresh_token(token: str) -> str:
    """
    Хэш refresh-токена (SHA-256 + pepper).
    ← ИЗМЕНЕНО: добавлен pepper.
    """
    data = (token + settings.refresh_pepper).encode()
    return hashlib.sha256(data).hexdigest()


def _generate_refresh_token() -> str:
    """Сгенерировать случайный refresh-токен (высокая энтропия)"""
    return secrets.token_urlsafe(48)


class AuthService:
    """Сервис аутентификации"""

    def __init__(self, db: Session = None):
        self.db = db or get_db_session()
        self._own_session = db is None

    def close(self):
        if self._own_session and self.db:
            self.db.close()

    # ==================== ЛОГИН ====================

    def authenticate(self, username: str, password: str) -> Optional[MobileUser]:
        """Проверить логин/пароль"""
        user = self.db.query(MobileUser).filter(
            MobileUser.user_id == username
        ).first()

        if not user:
            logger.warning(f"User not found: {username}")
            return None

        if not user.is_active:
            logger.warning(f"User inactive: {username}")
            return None

        if not verify_password(password, user.password_hash):
            logger.warning(f"Invalid password for: {username}")
            return None

        return user

    def create_session(
        self,
        user: MobileUser,
        user_agent: str = None,
        ip_address: str = None
    ) -> Dict[str, Any]:
        """Создать новую сессию: access + refresh"""
        # 1. Access-токен (JWT)
        access = create_access_token(
            user_id=user.user_id,
            username=user.user_id,
            department=user.department or '',
            role=user.role or 'doctor',
        )

        # 2. Refresh-токен (случайная строка)
        refresh_token = _generate_refresh_token()
        refresh_hash = _hash_refresh_token(refresh_token)

        # 3. Сохраняем сессию в БД
        expires_at = datetime.utcnow() + timedelta(days=settings.jwt_refresh_ttl_days)

        session = UserSession(
            user_id=user.user_id,
            access_jti=access['jti'],
            refresh_token_hash=refresh_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            is_revoked=False,  # ← явно
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Session created for {user.user_id} (session_id={session.id})")

        return {
            'access_token': access['token'],
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': access['expires_in'],
            'session_id': session.id,
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'full_name': user.full_name,
                'department': user.department,
                'role': user.role,
            }
        }

    # ==================== REFRESH ====================

    def refresh_session(
        self,
        refresh_token: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Обновить пару токенов по refresh-токену.

        ← ИЗМЕНЕНО:
        - Ротация с сохранением старой сессии (is_revoked=True), НЕ DELETE
        - Reuse detection: если пришёл revoked refresh → отзываем ВСЕ сессии
        - Проверка user_agent (логируется, не блокирует)
        - Принимает user_agent/ip для сохранения в новой сессии
        """
        refresh_hash = _hash_refresh_token(refresh_token)

        session = self.db.query(UserSession).filter(
            UserSession.refresh_token_hash == refresh_hash
        ).first()

        if not session:
            # Токен не найден вообще.
            # В теории это может быть старый refresh, который мы уже удалили
            # (если не храним revoked). Логируем, но не отзываем всё —
            # может быть просто опечатка/устаревший клиент.
            logger.warning("Refresh token not found in DB")
            return None

        # REUSE DETECTION: токен найден, но уже отозван → кража
        if session.is_revoked:
            logger.error(
                f"⚠️ REFRESH TOKEN REUSE DETECTED for user {session.user_id}! "
                f"Revoking ALL sessions."
            )
            self.revoke_all_user_sessions(session.user_id)
            return None

        if session.expires_at < datetime.utcnow():
            logger.warning(f"Refresh token expired for user {session.user_id}")
            session.is_revoked = True
            session.revoked_at = datetime.utcnow()
            self.db.commit()
            return None

        user = self.db.query(MobileUser).filter(
            MobileUser.user_id == session.user_id
        ).first()

        if not user or not user.is_active:
            logger.warning(f"User inactive or not found: {session.user_id}")
            session.is_revoked = True
            session.revoked_at = datetime.utcnow()
            self.db.commit()
            return None

        # Логируем смену User-Agent (не блокируем — мобильные клиенты меняются)
        if user_agent and session.user_agent and user_agent != session.user_agent:
            logger.warning(
                f"User-Agent changed for {session.user_id}: "
                f"'{session.user_agent}' → '{user_agent}'"
            )

        # РОТАЦИЯ: помечаем старую сессию revoked, НЕ удаляем
        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        self.db.commit()

        # Создаём новую сессию (новый jti, новый refresh)
        return self.create_session(
            user=user,
            user_agent=user_agent or session.user_agent,
            ip_address=ip_address or session.ip_address,
        )

    # ==================== LOGOUT ====================

    def revoke_session(self, refresh_token: str) -> bool:
        """
        Отозвать сессию по refresh-токену.
        ← ИЗМЕНЕНО: помечаем is_revoked, НЕ удаляем (для reuse detection).
        """
        refresh_hash = _hash_refresh_token(refresh_token)

        session = self.db.query(UserSession).filter(
            UserSession.refresh_token_hash == refresh_hash,
            UserSession.is_revoked == False,
        ).first()

        if not session:
            return False

        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"Session revoked for user {session.user_id}")
        return True

    def revoke_by_jti(self, access_jti: str) -> bool:
        """
        Отозвать сессию по jti access-токена.
        ← ИЗМЕНЕНО: помечаем is_revoked, НЕ удаляем.
        """
        session = self.db.query(UserSession).filter(
            UserSession.access_jti == access_jti,
            UserSession.is_revoked == False,
        ).first()

        if not session:
            return False

        session.is_revoked = True
        session.revoked_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"Session revoked by jti for user {session.user_id}")
        return True

    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Отозвать ВСЕ сессии пользователя (logout-all, смена пароля, reuse)"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False,
        ).all()

        count = len(sessions)
        now = datetime.utcnow()
        for s in sessions:
            s.is_revoked = True
            s.revoked_at = now

        self.db.commit()
        logger.info(f"Revoked {count} sessions for user {user_id}")
        return count

    # ==================== ПРОВЕРКА ====================

    def is_session_active(self, access_jti: str) -> bool:
        """
        Проверить, что сессия не отозвана.
        ← ИЗМЕНЕНО: убрана проверка expires_at (сессия живёт дольше access-токена).
        """
        session = self.db.query(UserSession).filter(
            UserSession.access_jti == access_jti,
            UserSession.is_revoked == False,
        ).first()
        return session is not None

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Список активных сессий пользователя"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False,
            UserSession.expires_at > datetime.utcnow(),
        ).order_by(UserSession.created_at.desc()).all()

        return [
            {
                'session_id': s.id,
                'created_at': s.created_at.isoformat() if s.created_at else None,
                'expires_at': s.expires_at.isoformat() if s.expires_at else None,
                'user_agent': s.user_agent,
                'ip_address': s.ip_address,
            }
            for s in sessions
        ]

    # ==================== CLEANUP ====================

    def cleanup_expired_sessions(self, keep_revoked_days: int = None) -> int:
        """
        Удалить старые сессии.
        ← ИЗМЕНЕНО: revoked храним дольше (для reuse detection),
        истёкшие не-revoked удаляем сразу.
        """
        keep_days = keep_revoked_days or settings.revoked_session_keep_days
        now = datetime.utcnow()

        # 1) Истёкшие и не revoked — можно удалять сразу
        expired = self.db.query(UserSession).filter(
            UserSession.expires_at < now,
            UserSession.is_revoked == False,
        ).all()

        # 2) Revoked — удаляем только если старше keep_days
        old_revoked_cutoff = now - timedelta(days=keep_days)
        old_revoked = self.db.query(UserSession).filter(
            UserSession.is_revoked == True,
            UserSession.revoked_at < old_revoked_cutoff,
        ).all()

        count = len(expired) + len(old_revoked)
        for s in expired + old_revoked:
            self.db.delete(s)

        self.db.commit()
        logger.info(
            f"Cleaned up {count} sessions "
            f"(expired={len(expired)}, old_revoked={len(old_revoked)})"
        )
        return count


# ==================== ХЕЛПЕРЫ ====================

def create_user_with_password(
    db: Session,
    user_id: str,
    password: str,
    full_name: str = '',
    department: str = '',
    role: str = 'doctor',
) -> MobileUser:
    """Создать пользователя с паролем (для админки)"""
    user = MobileUser(
        user_id=user_id,
        username=user_id,
        full_name=full_name,
        department=department,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user