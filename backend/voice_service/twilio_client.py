# voice_service/twilio_client.py
"""
Клиент Twilio для исходящих звонков.
"""
import logging
from typing import Optional

from twilio.rest import Client as TwilioRestClient
from twilio.base.exceptions import TwilioRestException

from config import settings

logger = logging.getLogger(__name__)


class TwilioClient:
    """Обёртка над Twilio REST API."""

    def __init__(self):
        if not settings.is_twilio_configured():
            logger.warning("Twilio не настроен — звонки работать не будут")
            self.client = None
        else:
            self.client = TwilioRestClient(
                settings.twilio_account_sid,
                settings.twilio_auth_token,
            )

    def make_call(
        self,
        to: str,
        phrase_text: str,
        phrase_audio_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        Совершить звонок.

        Returns:
            SID звонка или None, если ошибка.
        """
        if not self.client:
            logger.error("Twilio client не инициализирован")
            return None

        if settings.voice_test_number:
            logger.info(f"Тестовый режим: звоним на {settings.voice_test_number} вместо {to}")
            to = settings.voice_test_number

        if phrase_audio_url:
            twiml = f'<Response><Play>{phrase_audio_url}</Play></Response>'
        else:
            safe_text = (
                phrase_text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
            )
            twiml = (
                f'<Response>'
                f'<Say voice="Polly.Tatyana" language="ru-RU">{safe_text}</Say>'
                f'</Response>'
            )

        try:
            call = self.client.calls.create(
                to=to,
                from_=settings.twilio_from_number,
                twiml=twiml,
                timeout=settings.voice_call_timeout,
                status_callback=f"{settings.voice_public_url}/twilio/status",
                status_callback_event=[
                    'initiated', 'ringing', 'answered', 'completed'
                ],
                status_callback_method='POST',
            )

            logger.info(f"Twilio call created: {call.sid} → {to}")
            return call.sid

        except TwilioRestException as e:
            logger.error(
                f"Twilio error: code={e.code}, status={e.status}, msg={e.msg}"
            )
            return None

        except Exception as e:
            logger.error(f"Twilio unexpected error: {e}")
            return None


twilio_client = TwilioClient()