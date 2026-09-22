# app/auth/password.py
import os
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ← НОВОЕ: pepper — общий секрет, добавляемый к паролю перед хэшированием.
# Защищает, если БД утечёт, но env — нет.
PASSWORD_PEPPER = os.environ.get('PASSWORD_PEPPER', '')


def hash_password(password: str) -> str:
    """Захэшировать пароль (с pepper)"""
    return pwd_context.hash(password + PASSWORD_PEPPER)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Проверить пароль против хэша (с pepper)"""
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password + PASSWORD_PEPPER, password_hash)
    except Exception:
        return False