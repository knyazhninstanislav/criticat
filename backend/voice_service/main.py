# voice_service/main.py
"""
FastAPI-приложение voice-сервиса.

Отвечает за:
- health-check
- приём вебхуков от Twilio (статус звонка)
- отдачу аудиофайлов для <Play>
"""
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, Form, Response, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from config import settings
from database import init_db
from call_state import update_call_status, get_call_by_sid
from twilio_client import twilio_client
from rabbitmq_client import rabbitmq_client

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

TTS_CACHE_DIR = "data/tts_cache"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение."""
    logger.info("=" * 60)
    logger.info("VOICE SERVICE (FastAPI) СТАРТ")
    logger.info(f"Twilio: {'настроен' if settings.is_twilio_configured() else 'НЕ НАСТРОЕН'}")
    logger.info(f"TTS: {settings.tts_provider}")
    logger.info("=" * 60)

    init_db()

    # Подключаемся к RabbitMQ (для публикации failed)
    await rabbitmq_client.connect()

    yield

    logger.info("Voice Service завершает работу...")
    await rabbitmq_client.close()


app = FastAPI(
    title="CritiCat Voice Service",
    description="Сервис обзвона для критических результатов",
    version="1.0.0",
    lifespan=lifespan,
)


# ==================== HEALTH ====================

@app.get("/health")
async def health():
    """Health-check для Docker healthcheck."""
    return {
        "status": "ok",
        "service": "voice",
        "twilio_configured": settings.is_twilio_configured(),
        "rabbitmq_connected": rabbitmq_client.is_connected(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/")
async def root():
    return {
        "name": "CritiCat Voice Service",
        "version": "1.0.0",
        "status": "running",
    }


# ==================== TWILIO WEBHOOKS ====================

@app.post("/twilio/status")
async def twilio_status_webhook(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: str = Form(None),
    To: str = Form(None),
    From: str = Form(None),
    ErrorCode: str = Form(None),
    ErrorMessage: str = Form(None),
):
    """
    Вебхук от Twilio: статус звонка изменился.

    Twilio будет дёргать этот эндпоинт несколько раз:
    initiated → ringing → in-progress → completed
    """
    logger.info(
        f"Twilio webhook: SID={CallSid}, status={CallStatus}, "
        f"duration={CallDuration}, error={ErrorCode}"
    )

    # Обновляем в БД
    duration = int(CallDuration) if CallDuration and CallDuration.isdigit() else None

    update_call_status(
        twilio_sid=CallSid,
        status=CallStatus,
        duration_seconds=duration,
        error_code=ErrorCode,
        error_message=ErrorMessage,
    )

    return {"ok": True}


@app.post("/twilio/voice")
async def twilio_voice_webhook(
    CallSid: str = Form(...),
    From: str = Form(None),
    To: str = Form(None),
):
    """
    Twilio дёргает этот эндпоинт, когда трубку взяли.
    Возвращаем TwiML с текстом для проигрывания.

    Но у нас уже есть twiml при создании звонка, так что этот хук —
    на случай, если понадобится динамика (например, для эскалации).
    """
    logger.info(f"Twilio voice webhook: SID={CallSid}, from={From}, to={To}")

    call = get_call_by_sid(CallSid)
    if not call:
        logger.warning(f"Звонок {CallSid} не найден в БД")
        return PlainTextResponse(
            content='<Response><Say language="ru-RU">Ошибка</Say></Response>',
            media_type="application/xml",
        )

    # Для PoC просто вешаем трубку — основной TwiML уже был передан при создании
    twiml = '<Response><Hangup/></Response>'
    return PlainTextResponse(content=twiml, media_type="application/xml")


# ==================== AUDIO ====================

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Отдать аудиофайл для Twilio <Play>.

    В проде лучше отдавать через S3/CDN, но для PoC — FastAPI.
    """
    # Защита от path traversal
    if '..' in filename or '/' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = os.path.join(TTS_CACHE_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio not found")

    return FileResponse(
        filepath,
        media_type="audio/ogg",
        filename=filename,
    )


# ==================== MANUAL TRIGGER (для теста) ====================

@app.post("/test/call")
async def test_call(
    request: Request,
    phone: str = Form(...),
    phrase_key: str = Form('critical_department'),
):
    """
    Ручной триггер звонка для теста.

    curl -X POST http://localhost:8081/test/call \
        -F "phone=+79001234567" \
        -F "phrase_key=critical_department"
    """
    from phrases import get_phrase

    api_key = request.headers.get('X-API-Key')
    if api_key != settings.voice_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    phrase_text = get_phrase(phrase_key)

    twilio_sid = twilio_client.make_call(
        to=phone,
        phrase_text=phrase_text,
    )

    if not twilio_sid:
        raise HTTPException(status_code=500, detail="Failed to create call")

    return {
        "success": True,
        "twilio_sid": twilio_sid,
        "to": settings.voice_test_number or phone,
    }