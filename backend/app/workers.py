import logging
import asyncio
import json
from datetime import datetime
import redis
from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal, AnonymizedResult, TelegramUser, NotificationLog
from .telegram_bot import TelegramBot

logger = logging.getLogger(__name__)

class ResultWorker:
    """Worker для обработки результатов"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.telegram_bot = TelegramBot(settings.telegram_token)
    
    async def process_new_results(self):
        """Обработка новых результатов"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('criticat:new_results')
        
        logger.info("Worker запущен, ожидание результатов...")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    await self._process_result(data)
                except Exception as e:
                    logger.error(f"Ошибка обработки: {e}")
    
    async def _process_result(self, data: dict):
        """Обработка одного результата"""
        db = SessionLocal()
        
        try:
            # Получаем активных пользователей
            users = db.query(TelegramUser).filter(
                TelegramUser.is_active == True
            ).all()
            
            if not users:
                logger.warning("Нет активных пользователей")
                return
            
            # Отправляем уведомления
            for user in users:
                message_id = await self.telegram_bot.send_result_notification(
                    user.chat_id,
                    {'ids': data['ids'], 'department': data['department'], 
                     'results': [data]},
                    [data['result_key']]
                )
                
                if message_id:
                    # Обновляем БД
                    result = db.query(AnonymizedResult).filter(
                        AnonymizedResult.result_key == data['result_key']
                    ).first()
                    
                    if result:
                        result.status = 'sent'
                        result.telegram_message_id = message_id
                        result.telegram_chat_id = user.chat_id
                        
                        # Логируем
                        log = NotificationLog(
                            result_id=result.id,
                            result_key=data['result_key'],
                            chat_id=user.chat_id,
                            message_id=message_id,
                            action='sent'
                        )
                        db.add(log)
                
                db.commit()
        
        finally:
            db.close()

async def main():
    """Основная функция"""
    worker = ResultWorker()
    await worker.process_new_results()

if __name__ == "__main__":
    asyncio.run(main())