# app/main.py
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db, engine
from .api import router
from .rabbitmq_client import rabbitmq_client

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def rabbitmq_keepalive():
    """Фоновая задача для постоянной проверки и переподключения RabbitMQ"""
    while True:
        try:
            await asyncio.sleep(10)

            if not rabbitmq_client.is_connected():
                logger.warning("RabbitMQ connection lost, reconnecting...")
                await rabbitmq_client.connect()
        except asyncio.CancelledError:
            logger.info("Keepalive task cancelled")
            break
        except Exception as e:
            logger.error(f"Keepalive error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan менеджер"""
    logger.info("=" * 50)
    logger.info("Инициализация CritiCat Server...")
    logger.info("=" * 50)

    # Инициализация БД
    init_db()

    # Подключение к RabbitMQ (с retry)
    connected = await rabbitmq_client.ensure_connected(max_wait=30)
    if not connected:
        logger.error("❌ Could not connect to RabbitMQ after 30s, will keep trying...")
    else:
        logger.info("✅ RabbitMQ connected")

    # Запускаем фоновую задачу для keepalive
    keepalive_task = asyncio.create_task(rabbitmq_keepalive())

    logger.info("=" * 50)
    logger.info("CritiCat Server запущен")
    logger.info("=" * 50)

    yield

    # Shutdown
    logger.info("Shutting down...")
    keepalive_task.cancel()
    try:
        await keepalive_task
    except asyncio.CancelledError:
        pass
    await rabbitmq_client.close()
    logger.info("CritiCat Server остановлен")


app = FastAPI(
    title="CritiCat Server",
    description="Сервер для обработки критических результатов",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Корневой эндпоинт — показывает реальное состояние"""
    rabbitmq_ok = rabbitmq_client.is_connected()
    db_ok = engine is not None

    return {
        "name": "CritiCat Server",
        "version": "1.0.0",
        "status": "running" if (rabbitmq_ok and db_ok) else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "rabbitmq": "connected" if rabbitmq_ok else "disconnected",
    }


@app.get("/health")
async def health_check(response: Response):
    """
    Healthcheck — возвращает 503 если RabbitMQ или БД недоступны.
    Это заставляет Docker/K8s перезапускать контейнер.
    """
    import datetime

    db_ok = False
    try:
        from .database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_ok = True
    except Exception as e:
        logger.error(f"DB health check failed: {e}")

    rabbitmq_ok = rabbitmq_client.is_connected()

    healthy = db_ok and rabbitmq_ok

    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if healthy else "unhealthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "checks": {
            "database": "ok" if db_ok else "fail",
            "rabbitmq": "ok" if rabbitmq_ok else "fail",
        }
    }


@app.get("/health/live")
async def liveness():
    """Liveness — приложение живо (не проверяет зависимости)"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness(response: Response):
    """Readiness — приложение готово принимать трафик"""
    rabbitmq_ok = rabbitmq_client.is_connected()

    if not rabbitmq_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "rabbitmq": "disconnected"}

    return {"status": "ready", "rabbitmq": "connected"}