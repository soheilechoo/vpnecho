import sys
import os
import asyncio
import logging

# Create necessary directories
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Get token from environment
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    logger.error("BOT_TOKEN not found in environment variables!")
    sys.exit(1)

# Initialize bot
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Main menu keyboard
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟣 خرید VPN VIP", callback_data="buy_vip"),
            InlineKeyboardButton(text="🔵 خرید VPN معمولی", callback_data="buy_normal")
        ],
        [
            InlineKeyboardButton(text="🎓 آموزش", callback_data="tutorials")
        ],
        [
            InlineKeyboardButton(text="💰 موجودی و افزایش موجودی", callback_data="wallet"),
            InlineKeyboardButton(text="🎧 پشتیبانی", callback_data="support")
        ],
        [
            InlineKeyboardButton(text="👤 پروفایل من", callback_data="profile")
        ]
    ])

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Handle /start command"""
    user = message.from_user
    welcome_text = (
        f"👋 {user.first_name} عزیز به ربات فروش VPN خوش آمدید! 🌟\n\n"
        f"💰 موجودی حساب شما: 0 تومان\n\n"
        f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard()
    )

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    """Handle all callback queries"""
    data = callback.data
    
    if data == "main_menu":
        await callback.message.edit_text(
            "🏠 منوی اصلی",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return
    
    if data == "buy_vip":
        await callback.message.edit_text(
            "🟣 خرید VPN VIP\n\nلطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="👤 تک کاربره", callback_data="vip_single"),
                    InlineKeyboardButton(text="👥 دو کاربره", callback_data="vip_dual")
                ],
                [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        return
    
    if data == "buy_normal":
        await callback.message.edit_text(
            "🔵 خرید VPN معمولی\n\nلطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="👤 تک کاربره", callback_data="normal_single"),
                    InlineKeyboardButton(text="👥 دو کاربره", callback_data="normal_dual")
                ],
                [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        return
    
    if data in ["vip_single", "vip_dual", "normal_single", "normal_dual"]:
        product_names = {
            "vip_single": "VPN VIP تک کاربره",
            "vip_dual": "VPN VIP دو کاربره",
            "normal_single": "VPN معمولی تک کاربره",
            "normal_dual": "VPN معمولی دو کاربره"
        }
        prices = {
            "vip_single": 250,
            "vip_dual": 450,
            "normal_single": 190,
            "normal_dual": 270
        }
        
        await callback.message.edit_text(
            f"📋 تأیید خرید\n\n"
            f"🛒 محصول: {product_names[data]}\n"
            f"💰 قیمت: {prices[data]:,} تومان\n"
            f"💳 موجودی فعلی: 0 تومان\n"
            f"❌ موجودی کافی نیست!\n\n"
            f"لطفاً ابتدا حساب خود را شارژ کنید.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 افزایش موجودی", callback_data="deposit")],
                [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        return
    
    if data == "wallet":
        await callback.message.edit_text(
            "💰 مدیریت کیف پول\n\n"
            "💳 موجودی فعلی: 0 تومان\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 موجودی من", callback_data="balance")],
                [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
                [InlineKeyboardButton(text="📜 تاریخچه تراکنش‌ها", callback_data="transactions")],
                [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        return
    
    if data == "deposit":
        await callback.message.edit_text(
            "💳 افزایش موجودی\n\n"
            "لطفاً مبلغ مورد نظر را به تومان وارد کنید:\n\n"
            "📌 حداقل مبلغ: 1,000 تومان\n"
            "📌 حداکثر مبلغ: 10,000,000 تومان\n\n"
            "مبلغ را به تومان وارد کنید (فقط عدد):"
        )
        await callback.answer()
        return
    
    if data == "support":
        await callback.message.edit_text(
            "🎧 پشتیبانی\n\n"
            "برای ارتباط با پشتیبانی با @EchoVpnShopBot تماس بگیرید.\n\n"
            "📱 یوزرنیم پشتیبانی: @EchoVpnShopBot",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        return
    
    if data == "profile":
        await callback.message.edit_text(
            "👤 پروفایل کاربری\n\n"
            f"🆔 شناسه: {callback.from_user.id}\n"
            f"👤 نام: {callback.from_user.first_name or 'نامشخص'}\n"
            f"📱 یوزرنیم: @{callback.from_user.username or 'ندارد'}\n\n"
            f"💰 موجودی: 0 تومان\n"
            f"📊 تعداد سفارش‌ها: 0\n"
            f"✅ تکمیل‌شده: 0\n"
            f"❌ لغو‌شده: 0\n"
            f"💳 مجموع خرید: 0 تومان\n"
            f"💵 مجموع شارژ: 0 تومان",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        return
    
    if data == "balance":
        await callback.message.edit_text(
            "💰 موجودی حساب شما\n\n"
            "💳 موجودی فعلی: 0 تومان\n\n"
            "برای افزایش موجودی روی دکمه زیر کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
                [InlineKeyboardButton(text="↩️ بازگشت", callback_data="wallet")]
            ])
        )
        await callback.answer()
        return
    
    if data == "transactions":
        await callback.message.edit_text(
            "📜 تاریخچه تراکنش‌ها\n\n"
            "هیچ تراکنشی یافت نشد.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ بازگشت", callback_data="wallet")]
            ])
        )
        await callback.answer()
        return
    
    if data == "tutorials":
        await callback.message.edit_text(
            "🎓 آموزش‌ها\n\n"
            "هیچ آموزشی یافت نشد.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
            ])
        )
        await callback.answer()
        return
    
    await callback.answer("در حال توسعه...")

async def main():
    """Main function"""
    logger.info("🚀 Starting bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Bot stopped with error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
