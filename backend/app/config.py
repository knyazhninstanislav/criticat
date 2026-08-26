import os
from typing import Optional

class Settings:
    """Настройки приложения"""
    
    def __init__(self):
        # Telegram
        self.telegram_token: str = os.environ.get('TELEGRAM_TOKEN', '')
        
        # База данных
        self.database_url: str = os.environ.get('DATABASE_URL', 'sqlite:///data/criticat.db')
        
        # Redis
        self.redis_url: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        
        # JWT
        self.jwt_secret: str = os.environ.get('JWT_SECRET', 'default-secret-key')
        
        # Логирование
        self.log_level: str = os.environ.get('LOG_LEVEL', 'INFO')

settings = Settings()