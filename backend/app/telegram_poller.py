import asyncio
import logging
from .config import settings
from .telegram_bot import TelegramBot

logger = logging.getLogger(__name__)

async def main():
    """Запуск polling для Telegram бота"""
    bot = TelegramBot(settings.telegram_token)
    await bot.register_handlers()
    
    logger.info("Telegram Poller запущен")
    
    # Запускаем polling
    bot.start_polling()

if __name__ == "__main__":
    asyncio.run(main())