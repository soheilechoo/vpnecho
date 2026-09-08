from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from app.services.user_service import UserService
from app.database.session import get_db_session
import logging

logger = logging.getLogger(__name__)

class UserRegisterMiddleware(BaseMiddleware):
    """میان‌افزار ثبت خودکار کاربر"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # دریافت کاربر تلگرام
        if isinstance(event, Message):
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user
        else:
            return await handler(event, data)
        
        if not telegram_user:
            return await handler(event, data)
        
        # ثبت یا بروزرسانی کاربر
        with get_db_session() as db:
            user_service = UserService(db)
            user = user_service.register_or_update_user(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                is_bot=telegram_user.is_bot,
                is_premium=getattr(telegram_user, 'is_premium', False)
            )
            
            # ذخیره کاربر در data برای دسترسی هندلرها
            data['user'] = user
            data['bot_data'] = {'user': user}
        
        return await handler(event, data)
