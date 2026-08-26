import logging
from typing import List, Dict, Any, Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramBot:
    """Класс для работы с Telegram ботом"""
    
    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(token=token)
        self.application = Application.builder().token(token).build()
    
    async def send_result_notification(
        self,
        chat_id: str,
        result_data: Dict[str, Any],
        result_keys: List[str]
    ) -> Optional[str]:
        """Отправка уведомления о критическом результате"""
        try:
            message = self._format_message(result_data)
            reply_markup = self._create_reply_markup(result_keys)
            
            sent_message = await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            return str(sent_message.message_id)
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def _format_message(self, data: Dict[str, Any]) -> str:
        """Форматирование сообщения (только обезличенные данные)"""
        message = f"🚨 <b>КРИТИЧЕСКОЕ ОТКЛОНЕНИЕ!</b>\n\n"
        message += f"🆔 <b>IDS:</b> {data['ids']}\n"
        message += f"🏥 <b>Отделение:</b> {data['department']}\n\n"
        
        for result in data['results']:
            message += f"🧪 <b>{result['test_name']}</b>\n"
            message += f"   Значение: <b>{result['result_value']:.2f}</b>\n"
            
            if result.get('ref_lower') and result.get('ref_upper'):
                message += f"   Норма: {result['ref_lower']:.2f} - {result['ref_upper']:.2f}\n"
            
            if result.get('deviation_percent'):
                message += f"   Отклонение: <b>{result['deviation_percent']:.1f}%</b>\n"
            
            message += "\n"
        
        message += "⚠️ <i>Требуется подтверждение</i>"
        return message
    
    def _create_reply_markup(self, result_keys: List[str]) -> InlineKeyboardMarkup:
        """Создание клавиатуры для подтверждения"""
        keyboard = []
        
        # Кнопка "Принять все"
        if len(result_keys) > 1:
            all_keys = ','.join(result_keys)
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ Принять все ({len(result_keys)})",
                    callback_data=f"accept_all:{all_keys}"
                )
            ])
        
        # Кнопки для каждого результата
        for i, key in enumerate(result_keys, 1):
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ Принять результат {i}",
                    callback_data=f"accept:{key}"
                )
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def register_handlers(self):
        """Регистрация обработчиков"""
        self.application.add_handler(
            CallbackQueryHandler(self._handle_callback)
        )
        self.application.add_handler(
            CommandHandler("start", self._handle_start)
        )
    
    async def _handle_callback(self, update, context):
        """Обработка callback"""
        query = update.callback_query
        await query.answer("✅ Результат принят")
        
        data = query.data
        chat_id = str(query.message.chat_id)
        
        if data.startswith("accept_all:"):
            keys = data.split(':')[1].split(',')
            await self._process_confirmation(keys, chat_id)
        elif data.startswith("accept:"):
            key = data.split(':')[1]
            await self._process_confirmation([key], chat_id)
    
    async def _process_confirmation(self, keys: List[str], chat_id: str):
        """Обработка подтверждения"""
        # Здесь будет сохранение в БД и отправка в Redis
        logger.info(f"Подтверждение результатов {keys} от {chat_id}")
    
    async def _handle_start(self, update, context):
        """Обработка команды /start"""
        await update.message.reply_text(
            "👋 Здравствуйте!\n"
            "Я бот для уведомления о критических результатах.\n"
            "Вы будете получать уведомления о критических отклонениях."
        )
    
    def start_polling(self):
        """Запуск polling"""
        self.application.run_polling()