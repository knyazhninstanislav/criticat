from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import settings
from .database import init_db
from .api import router

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание приложения
app = FastAPI(
    title="CritiCat Server",
    description="Сервер для обработки критических результатов",
    version="1.0.0"
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

@app.on_event("startup")
async def startup_event():
    """Инициализация при старте"""
    logger.info("Инициализация базы данных...")
    init_db()
    logger.info("CritiCat Server запущен")

@app.on_event("shutdown")
async def shutdown_event():
    """Действия при остановке"""
    logger.info("CritiCat Server остановлен")

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "name": "CritiCat Server",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "ok",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }