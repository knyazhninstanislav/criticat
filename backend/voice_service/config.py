# voice_service/config.py
import os
import logging
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    """Настройки voice-сервиса."""

    def __init__(self):
        # === Twilio ===
        self.twilio_account_sid: str = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token: str = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.twilio_from_number: str = os.environ.get('TWILIO_FROM_NUMBER', '')
        self.voice_public_url: str = os.environ.get('VOICE_PUBLIC_URL', 'http://localhost:8081')

        # === TTS ===
        self.tts_provider: str = os.environ.get('TTS_PROVIDER', 'twilio').lower()
        self.yandex_tts_api_key: str = os.environ.get('YANDEX_TTS_API_KEY', '')
        self.yandex_tts_folder_id: str = os.environ.get('YANDEX_TTS_FOLDER_ID', '')

        # === RabbitMQ ===
        self.rabbitmq_host: str = os.environ.get('RABBITMQ_HOST', 'localhost')
        self.rabbitmq_port: int = int(os.environ.get('RABBITMQ_PORT', 5672))
        self.rabbitmq_user: str = os.environ.get('RABBITMQ_USER', 'guest')
        self.rabbitmq_password: str = os.environ.get('RABBITMQ_PASSWORD', 'guest')
        self.rabbitmq_vhost: str = os.environ.get('RABBITMQ_VHOST', '/')

        # Очереди (совпадают с основным API)
        self.exchange_main: str = 'lab.exchange'
        self.exchange_dlx: str = 'lab.dlx.exchange'
        self.queue_voice_calls: str = 'voice.calls.queue'
        self.queue_voice_failed: str = 'voice.failed.queue'
        self.routing_voice_call: str = 'voice.call'
        self.routing_voice_failed: str = 'voice.failed'

        # === БД voice-сервиса ===
        self.voice_db_url: str = os.environ.get('VOICE_DB_URL', 'sqlite:///data/voice.db')

        # === Логика ===
        self.voice_escalation_minutes: int = int(os.environ.get('VOICE_ESCALATION_MINUTES', 15))
        self.quiet_hours_start: int = int(os.environ.get('QUIET_HOURS_START', 22))
        self.quiet_hours_end: int = int(os.environ.get('QUIET_HOURS_END', 7))
        self.voice_max_attempts: int = int(os.environ.get('VOICE_MAX_ATTEMPTS', 3))
        self.voice_call_timeout: int = int(os.environ.get('VOICE_CALL_TIMEOUT', 30))
        self.voice_test_number: Optional[str] = os.environ.get('VOICE_TEST_NUMBER') or None

        # === API ===
        self.voice_api_key: str = os.environ.get('VOICE_API_KEY', 'change-me-in-production')

        # === Прочее ===
        self.env: str = os.environ.get('ENV', 'development').lower()
        self.log_level: str = os.environ.get('LOG_LEVEL', 'INFO').upper()

    def is_twilio_configured(self) -> bool:
        return bool(
            self.twilio_account_sid
            and self.twilio_auth_token
            and self.twilio_from_number
        )

    def is_quiet_hours_now(self) -> bool:
        """Проверка, попадаем ли в тихие часы."""
        from datetime import datetime
        hour = datetime.now().hour

        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= hour < self.quiet_hours_end
        else:
            return hour >= self.quiet_hours_start or hour < self.quiet_hours_end


settings = Settings()