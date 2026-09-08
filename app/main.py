import asyncio
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config.settings import settings
from app.database.session import engine
from app.database.base import Base
from app.middlewares.user_register import UserRegisterMiddleware
from app.middlewares.error_handler import ErrorHandlerMiddleware
from app.handlers.common import router as common_router
from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router
from app.handlers.support import router as support_router
from app.utils.helpers import setup_bot_commands

# تنظیم لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """نقطه ورود اصلی"""
    logger.info("شروع ربات ECHO VPN...")
    
    # ایجاد جداول دیتابیس
    Base.metadata.create_all(bind=engine)
    
    # راه‌اندازی بات
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # تنظیم دستورات
    await setup_bot_commands(bot)
    
    # راه‌اندازی دیسپچر
    dp = Dispatcher()
    
    # ثبت میان‌افزارها
    dp.message.middleware(UserRegisterMiddleware())
    dp.callback_query.middleware(UserRegisterMiddleware())
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    
    # ثبت روت‌ها
    dp.include_router(common_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(support_router)
    
    # ذخیره نمونه بات در دیسپچر
    dp["bot"] = bot
    
    # شروع پولینگ
    try:
        logger.info("ربات شروع به کار کرد...")
        logger.info(f"Admin IDs: {settings.ADMIN_IDS}")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("ربات توسط کاربر متوقف شد")
    except Exception as e:
        logger.error(f"خطا: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("اتصال بات بسته شد")

if __name__ == "__main__":
    asyncio.run(main())
