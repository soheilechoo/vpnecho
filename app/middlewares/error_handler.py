from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import logging

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseMiddleware):
    """میان‌افزار مدیریت خطا"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"خطا: {e}", exc_info=True)
            
            error_message = "❌ مشکلی در انجام عملیات رخ داد.\nاطلاعات شما از بین نرفته است.\nلطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            
            try:
                if isinstance(event, Message):
                    await event.answer(error_message)
                elif isinstance(event, CallbackQuery):
                    await event.answer("خطا در انجام عملیات", show_alert=True)
                    await event.message.edit_text(
                        error_message,
                        reply_markup=back_to_main_button()
                    )
            except:
                pass
            
            return None
