# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import asyncio
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db, engine
from .api import router
from .rabbitmq_client import rabbitmq_client

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan менеджер для управления жизненным циклом приложения"""
    # Startup
    logger.info("=" * 50)
    logger.info("Инициализация CritiCat Server...")
    logger.info("=" * 50)

    # Инициализация БД
    init_db()

    # Подключение к RabbitMQ
    if not await rabbitmq_client.connect():
        logger.warning("Could not connect to RabbitMQ")

    logger.info("=" * 50)
    logger.info("CritiCat Server запущен и готов к работе")
    logger.info("=" * 50)

    yield

    # Shutdown
    logger.info("CritiCat Server остановлен")
    await rabbitmq_client.close()


# Создание приложения
app = FastAPI(
    title="CritiCat Server",
    description="Сервер для обработки критических результатов",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "name": "CritiCat Server",
        "version": "1.0.0",
        "status": "running",
        "database": "connected" if engine else "not connected",
        "rabbitmq": "connected" if rabbitmq_client.is_connected() else "disconnected"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    import datetime
    return {
        "status": "ok",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "rabbitmq": "connected" if rabbitmq_client.is_connected() else "disconnected"
    }