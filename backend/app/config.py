# app/config.py
import os
import secrets
import logging

logger = logging.getLogger(__name__)


class Settings:
    """Настройки приложения"""

    def __init__(self):
        # База данных
        self.database_url: str = os.environ.get('DATABASE_URL', 'sqlite:///data/criticat.db')

        # API Key
        self.api_key: str = os.environ.get('API_KEY', 'default-secret-key')

        # ===== JWT =====
        # ← ИЗМЕНЕНО: не генерируем случайный секрет в проде
        env = os.environ.get('ENV', 'development').lower()
        jwt_secret = os.environ.get('JWT_SECRET')
        if not jwt_secret:
            if env == 'production':
                raise RuntimeError(
                    "JWT_SECRET must be set in production environment!"
                )
            jwt_secret = secrets.token_urlsafe(48)
            logger.warning(
                "JWT_SECRET not set — using random dev secret. "
                "All tokens will be invalid after restart!"
            )
        self.jwt_secret: str = jwt_secret
        self.jwt_algorithm: str = 'HS256'
        self.jwt_issuer: str = 'criticat'
        self.jwt_audience: str = 'criticat-api'  # ← НОВОЕ
        self.jwt_access_ttl_minutes: int = int(os.environ.get('JWT_ACCESS_TTL_MINUTES', 5))
        self.jwt_refresh_ttl_days: int = int(os.environ.get('JWT_REFRESH_TTL_DAYS', 30))

        # ← НОВОЕ: pepper для refresh-токенов (доп. защита при утечке БД)
        self.refresh_pepper: str = os.environ.get('REFRESH_PEPPER', '')

        # ← НОВОЕ: сколько дней хранить revoked-сессии (для reuse detection)
        self.revoked_session_keep_days: int = int(
            os.environ.get('REVOKED_SESSION_KEEP_DAYS', 7)
        )

        # Логирование
        self.log_level: str = os.environ.get('LOG_LEVEL', 'INFO')

        # RabbitMQ
        self.rabbitmq_host: str = os.environ.get('RABBITMQ_HOST', 'localhost')
        self.rabbitmq_port: int = int(os.environ.get('RABBITMQ_PORT', 5672))
        self.rabbitmq_user: str = os.environ.get('RABBITMQ_USER', 'guest')
        self.rabbitmq_password: str = os.environ.get('RABBITMQ_PASSWORD', 'guest')
        self.rabbitmq_vhost: str = os.environ.get('RABBITMQ_VHOST', '/')

        # Очереди
        self.queue_incoming: str = 'lab.critical.results'
        self.queue_app: str = 'alert.app.queue'
        self.queue_pending: str = 'pending.confirmation.queue'
        self.queue_response: str = 'user.response.queue'
        self.queue_rejected: str = 'rejected.results.queue'
        self.queue_desktop_confirmation: str = 'desktop.confirmation.queue'
        self.queue_retry_delay: str = 'retry.delay.queue'
        self.queue_failed: str = 'failed.alerts.queue'

        # Exchanges
        self.exchange_main: str = 'lab.exchange'
        self.exchange_dlx: str = 'lab.dlx.exchange'

        # Настройки очередей
        self.message_ttl: int = int(os.environ.get('MESSAGE_TTL', 60000))
        self.retry_delay: int = int(os.environ.get('RETRY_DELAY', 300000))
        self.max_retries: int = int(os.environ.get('MAX_RETRIES', 3))
        self.pending_timeout_hours: int = int(os.environ.get('PENDING_TIMEOUT_HOURS', 24))


settings = Settings()