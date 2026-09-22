# app/auth/jwt_utils.py
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from ..config import settings


def create_access_token(
    user_id: str,
    username: str,
    department: str,
    role: str,
    ttl_minutes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Создать access-токен (JWT).

    Returns:
        {
            'token': 'eyJhbGc...',
            'jti': 'uuid-токена',
            'expires_at': datetime истечения,
            'expires_in': секунды
        }
    """
    ttl = ttl_minutes or settings.jwt_access_ttl_minutes
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=ttl)
    jti = str(uuid.uuid4())

    # ← ИЗМЕНЕНО: добавлены aud и nbf
    payload = {
        'sub': username,
        'user_id': user_id,
        'username': username,
        'department': department,
        'role': role,
        'jti': jti,
        'iss': settings.jwt_issuer,
        'aud': settings.jwt_audience,
        'iat': int(now.timestamp()),
        'nbf': int(now.timestamp()),
        'exp': int(expires_at.timestamp()),
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return {
        'token': token,
        'jti': jti,
        'expires_at': expires_at,
        'expires_in': ttl * 60,
    }


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Проверить и декодировать access-токен.

    Проверяет: подпись, exp, iat, nbf, iss, aud.
    Returns payload если валиден, None если нет.
    """
    try:
        # ← ИЗМЕНЕНО: добавлены audience и nbf в проверку
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={
                "require": ["exp", "iat", "nbf", "sub", "jti", "iss", "aud"]
            }
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None