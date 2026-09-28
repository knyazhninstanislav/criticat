# voice_service/tts.py
"""
Генерация аудио из текста.

Для русского языка лучший вариант — Yandex SpeechKit.
Но для MVP можно использовать встроенный TTS Twilio (<Say>).
"""
import logging
import hashlib
import os
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

CACHE_DIR = "data/tts_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


async def generate_audio(text: str, voice: str = 'alena') -> Optional[str]:
    """
    Сгенерировать аудиофайл из текста через Yandex SpeechKit.

    Returns:
        Путь к файлу или None, если не удалось.
    """
    if not settings.yandex_tts_api_key or not settings.yandex_tts_folder_id:
        logger.warning("Yandex TTS не настроен")
        return None

    text_hash = hashlib.sha256(f"{voice}:{text}".encode()).hexdigest()[:16]
    cache_path = os.path.join(CACHE_DIR, f"{text_hash}.ogg")

    if os.path.exists(cache_path):
        logger.debug(f"TTS cache hit: {cache_path}")
        return cache_path

    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

    headers = {
        "Authorization": f"Api-Key {settings.yandex_tts_api_key}",
    }

    data = {
        "text": text,
        "lang": "ru-RU",
        "voice": voice,
        "folderId": settings.yandex_tts_folder_id,
        "format": "oggopus",
        "sampleRateHertz": "48000",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, data=data)
            if resp.status_code != 200:
                logger.error(f"Yandex TTS error: {resp.status_code} {resp.text}")
                return None

            with open(cache_path, 'wb') as f:
                f.write(resp.content)

        logger.info(f"TTS generated: {cache_path}")
        return cache_path

    except Exception as e:
        logger.error(f"TTS exception: {e}")
        return None


def get_audio_url(text: str, voice: str = 'alena') -> Optional[str]:
    """Получить публичный URL аудиофайла для Twilio."""
    text_hash = hashlib.sha256(f"{voice}:{text}".encode()).hexdigest()[:16]
    cache_path = os.path.join(CACHE_DIR, f"{text_hash}.ogg")

    if os.path.exists(cache_path):
        return f"{settings.voice_public_url}/audio/{os.path.basename(cache_path)}"

    return None