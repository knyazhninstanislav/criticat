# app/auth/dependencies.py
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from .jwt_utils import decode_access_token
from .service import AuthService

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    Получить текущего пользователя из JWT.

    ← ИЗМЕНЕНО: по умолчанию НЕ ходим в БД на каждый запрос.
    Проверяем только подпись/exp/iss/aud. Отзыв — через короткий TTL access-токена
    и (опционально) blacklist в Redis.

    Если нужен мгновенный отзыв — используйте get_current_user_sensitive.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или истёкший токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user_sensitive(
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ← НОВОЕ: версия get_current_user с проверкой сессии в БД.
    Используйте для sensitive-эндпоинтов (смена пароля, удаление и т.п.),
    где нужен мгновенный отзыв.
    """
    jti = user.get('jti')
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен без jti",
            headers={"WWW-Authenticate": "Bearer"},
        )

    service = AuthService()
    try:
        if not service.is_session_active(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия отозвана",
                headers={"WWW-Authenticate": "Bearer"},
            )
    finally:
        service.close()

    return user


async def require_role(role: str):
    """Dependency для проверки роли"""
    async def _checker(user: Dict[str, Any] = Depends(get_current_user)):
        if user.get('role') != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль: {role}",
            )
        return user
    return _checker


async def require_admin(user: Dict[str, Any] = Depends(get_current_user)):
    """Требуется роль admin"""
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора",
        )
    return user