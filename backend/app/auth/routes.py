# app/auth/routes.py
import logging
from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, Field
from typing import Optional, List

from .service import AuthService, create_user_with_password
from .dependencies import get_current_user, get_current_user_sensitive, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ==================== СХЕМЫ ====================

class LoginRequest(BaseModel):
    username: str = Field(..., description="Логин (user_id)")
    password: str = Field(..., description="Пароль")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh-токен")


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Refresh-токен")


class CreateUserRequest(BaseModel):
    user_id: str
    password: str
    full_name: Optional[str] = ''
    department: Optional[str] = ''
    role: Optional[str] = 'doctor'


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ==================== ЭНДПОИНТЫ ====================

@router.post("/login")
async def login(data: LoginRequest, request: Request):
    """
    Логин. Возвращает пару access + refresh.

    Пример:
    POST /api/v1/auth/login
    {
        "username": "ivanov",
        "password": "qwerty123"
    }
    """
    service = AuthService()
    try:
        user = service.authenticate(data.username, data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль",
            )

        user_agent = request.headers.get('user-agent', '')
        ip_address = request.client.host if request.client else None

        session = service.create_session(user, user_agent=user_agent, ip_address=ip_address)

        logger.info(f"Login successful: {data.username}")

        return {
            'success': True,
            **session,
        }

    finally:
        service.close()


@router.post("/refresh")
async def refresh(data: RefreshRequest, request: Request):
    """
    Обновить пару токенов по refresh-токену.
    Ротация: старый refresh помечается revoked, создаётся новый.
    Reuse detection: повторное использование revoked refresh → отзыв всех сессий.
    """
    service = AuthService()
    try:
        user_agent = request.headers.get('user-agent', '')
        ip_address = request.client.host if request.client else None

        session = service.refresh_session(
            data.refresh_token,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный или истёкший refresh-токен",
            )

        return {
            'success': True,
            **session,
        }

    finally:
        service.close()


@router.post("/logout")
async def logout(data: LogoutRequest, user: dict = Depends(get_current_user)):
    """
    Выйти из текущей сессии.

    Помечает refresh-токен как revoked.
    Access-токен умрёт сам через 5 минут (или через blacklist в Redis).
    """
    service = AuthService()
    try:
        if data.refresh_token:
            service.revoke_session(data.refresh_token)

        return {
            'success': True,
            'message': 'Вы вышли из системы',
        }

    finally:
        service.close()


@router.post("/logout-all")
async def logout_all(user: dict = Depends(get_current_user)):
    """
    Выйти из ВСЕХ сессий (все устройства).
    """
    service = AuthService()
    try:
        count = service.revoke_all_user_sessions(user.get('user_id'))

        return {
            'success': True,
            'message': f'Отозвано сессий: {count}',
            'revoked_count': count,
        }

    finally:
        service.close()


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """
    Информация о текущем пользователе.
    """
    return {
        'success': True,
        'user': {
            'user_id': user.get('user_id'),
            'username': user.get('username'),
            'department': user.get('department'),
            'role': user.get('role'),
        }
    }


@router.get("/sessions")
async def get_sessions(user: dict = Depends(get_current_user)):
    """
    Список активных сессий текущего пользователя.
    """
    service = AuthService()
    try:
        sessions = service.get_user_sessions(user.get('user_id'))
        return {
            'success': True,
            'sessions': sessions,
        }
    finally:
        service.close()


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: int, user: dict = Depends(get_current_user)):
    """
    Отозвать конкретную сессию по ID.
    """
    # TODO: реализовать проверку, что сессия принадлежит user
    raise HTTPException(status_code=501, detail="Пока не реализовано")


# ==================== АДМИНСКИЕ ====================

@router.post("/users")
async def create_user(
    data: CreateUserRequest,
    admin: dict = Depends(require_admin)
):
    """
    Создать пользователя с паролем (только для админов).
    """
    service = AuthService()
    try:
        from ..database import MobileUser
        existing = service.db.query(MobileUser).filter(
            MobileUser.user_id == data.user_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким user_id уже существует",
            )

        user = create_user_with_password(
            db=service.db,
            user_id=data.user_id,
            password=data.password,
            full_name=data.full_name,
            department=data.department,
            role=data.role,
        )

        logger.info(f"User created by admin: {data.user_id}")

        return {
            'success': True,
            'message': 'Пользователь создан',
            'user': {
                'user_id': user.user_id,
                'full_name': user.full_name,
                'department': user.department,
                'role': user.role,
                'is_active': user.is_active,
            }
        }

    finally:
        service.close()


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    user: dict = Depends(get_current_user_sensitive)  # ← ИЗМЕНЕНО: sensitive
):
    """
    Сменить свой пароль.
    ← ИЗМЕНЕНО: после смены пароля отзываем ВСЕ сессии пользователя.
    """
    from ..database import MobileUser
    from .password import verify_password, hash_password

    service = AuthService()
    try:
        db_user = service.db.query(MobileUser).filter(
            MobileUser.user_id == user.get('user_id')
        ).first()

        if not db_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        if not verify_password(data.old_password, db_user.password_hash):
            raise HTTPException(status_code=400, detail="Неверный старый пароль")

        db_user.password_hash = hash_password(data.new_password)
        service.db.commit()

        # ← ИЗМЕНЕНО: отзываем все сессии (включая текущую).
        # Клиент должен залогиниться заново.
        revoked = service.revoke_all_user_sessions(user.get('user_id'))

        logger.info(
            f"Password changed: {user.get('user_id')}, "
            f"revoked {revoked} sessions"
        )

        return {
            'success': True,
            'message': 'Пароль изменён. Войдите заново.',
            'revoked_sessions': revoked,
        }

    finally:
        service.close()