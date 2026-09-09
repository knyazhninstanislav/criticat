# config.py
import os


class Settings:
    """Настройки приложения"""

    def __init__(self):
        # Telegram
        self.telegram_token: str = os.environ.get('TELEGRAM_TOKEN', '')

        # База данных
        self.database_url: str = os.environ.get('DATABASE_URL', 'sqlite:///data/criticat.db')

        # API Key
        self.api_key: str = os.environ.get('API_KEY', 'default-secret-key')

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
        self.queue_telegram: str = 'alert.telegram.queue'
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
        self.message_ttl: int = int(os.environ.get('MESSAGE_TTL', 60000))  # 1 минута
        self.retry_delay: int = int(os.environ.get('RETRY_DELAY', 300000))  # 5 минут
        self.max_retries: int = int(os.environ.get('MAX_RETRIES', 3))
        self.pending_timeout_hours: int = int(os.environ.get('PENDING_TIMEOUT_HOURS', 24))


settings = Settings()