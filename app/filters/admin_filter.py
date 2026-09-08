from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from app.config.settings import settings

class AdminFilter(BaseFilter):
    """فیلتر دسترسی ادمین"""
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        if isinstance(event, Message):
            user_id = event.from_user.id
        else:
            user_id = event.from_user.id
        return user_id in settings.ADMIN_IDS
