# voice_service/worker_runner.py
"""
Точка входа для worker'а.
Запускается отдельно от FastAPI (в том же контейнере).
"""
import asyncio
import logging

from config import settings
from worker import run_worker

if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    asyncio.run(run_worker())