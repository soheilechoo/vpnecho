import sys
import os
import traceback
import asyncio

# ایجاد پوشه‌های لازم
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

print("=" * 50)
print("🚀 Starting VPN Bot...")
print("=" * 50)

try:
    # بارگذاری متغیرهای محیطی
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
    
    # ============================================
    # 🔴 توکن را در این قسمت قرار دهید (فقط یک خط)
    # ============================================
    
    # گزینه ۱: استفاده از Environment Variables (توصیه شده)
    TOKEN = os.getenv('BOT_TOKEN')
    
    # گزینه ۲: قرار دادن مستقیم توکن (اگر گزینه ۱ کار نکرد)
    # این خط را از حالت کامنت خارج کنید و توکن جدید را جایگزین کنید
    # و خط بالایی را کامنت کنید
    # TOKEN = "توکن_جدید_خود_را_اینجا_بگذارید"
    
    # ============================================
    
    if not TOKEN:
        print("❌ BOT_TOKEN not found in environment!")
        print("💡 Please set BOT_TOKEN in Render Environment Variables")
        print("💡 Or uncomment line 22 and add your token there")
        sys.exit(1)
    print("✅ BOT_TOKEN found")
    
    # ایمپورت aiogram - درست نوشته شده
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.enums import ParseMode
    print("✅ aiogram imported")
    
    # ایجاد ربات
    bot = Bot(
        token=TOKEN,
        parse_mode=ParseMode.HTML
    )
    dp = Dispatcher()
    print("✅ Bot and Dispatcher created")
    
    # ============ منوهای کیبورد ============
    
    def main_menu_keyboard():
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
    
    def get_back_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
        ])
    
    # ============ هندلرهای پیام ============
    
    @dp.message(Command("start"))
    async def start_command(message: types.Message):
        user = message.from_user
        await message.answer(
            f"👋 {user.first_name} عزیز به ربات فروش VPN خوش آمدید! 🌟\n\n"
            f"💰 موجودی حساب شما: 0 تومان\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=main_menu_keyboard()
        )
    
    @dp.message(Command("help"))
    async def help_command(message: types.Message):
        await message.answer(
            "🤖 راهنمای ربات:\n\n"
            "🟣 خرید VPN VIP - خرید اشتراک VIP\n"
            "🔵 خرید VPN معمولی - خرید اشتراک معمولی\n"
            "🎓 آموزش - مشاهده آموزش‌ها\n"
            "💰 موجودی - مدیریت کیف پول\n"
            "🎧 پشتیبانی - ارتباط با پشتیبانی",
            reply_markup=get_back_keyboard()
        )
    
    # ============ هندلرهای دکمه‌ها ============
    
    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery):
        data = callback.data
        user = callback.from_user
        
        # بازگشت به منوی اصلی
        if data == "main_menu":
            await callback.message.edit_text(
                f"🏠 منوی اصلی\n\n"
                f"👋 {user.first_name} عزیز خوش آمدید!",
                reply_markup=main_menu_keyboard()
            )
            await callback.answer()
            return
        
        # خرید VPN VIP
        if data == "buy_vip":
            await callback.message.edit_text(
                "🟣 خرید VPN VIP\n\n"
                "لطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
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
        
        # خرید VPN معمولی
        if data == "buy_normal":
            await callback.message.edit_text(
                "🔵 خرید VPN معمولی\n\n"
                "لطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
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
        
        # انتخاب محصول
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
        
        # کیف پول
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
        
        # افزایش موجودی
        if data == "deposit":
            await callback.message.edit_text(
                "💳 افزایش موجودی\n\n"
                "لطفاً مبلغ مورد نظر را به تومان وارد کنید:\n\n"
                "📌 حداقل مبلغ: 1,000 تومان\n"
                "📌 حداکثر مبلغ: 10,000,000 تومان\n\n"
                "مبلغ را به تومان وارد کنید (فقط عدد):",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="↩️ بازگشت", callback_data="wallet")]
                ])
            )
            await callback.answer()
            return
        
        # پشتیبانی
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
        
        # پروفایل
        if data == "profile":
            await callback.message.edit_text(
                "👤 پروفایل کاربری\n\n"
                f"🆔 شناسه: {user.id}\n"
                f"👤 نام: {user.first_name or 'نامشخص'}\n"
                f"📱 یوزرنیم: @{user.username or 'ندارد'}\n\n"
                f"💰 موجودی: 0 تومان\n"
                f"📊 تعداد سفارش‌ها: 0\n"
                f"✅ تکمیل‌شده: 0\n"
                f"❌ لغو‌شده: 0",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
                ])
            )
            await callback.answer()
            return
        
        # موجودی
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
        
        # تاریخچه تراکنش‌ها
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
        
        # آموزش‌ها
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
        
        # اگر هیچکدام نبود
        await callback.answer("⏳ در حال توسعه...")
    
    # ============ اجرای ربات ============
    
    async def main():
        print("=" * 50)
        print("✅ Bot is ready!")
        print("🤖 Starting polling...")
        print("=" * 50)
        await dp.start_polling(bot)
    
    print("=" * 50)
    print("✅ All imports successful!")
    print("🚀 Starting bot...")
    print("=" * 50)
    
    asyncio.run(main())
    
except Exception as e:
    print("=" * 50)
    print("❌ ERROR OCCURRED:")
    print("=" * 50)
    traceback.print_exc()
    print("=" * 50)
    print("💡 Error details:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {str(e)}")
    print("=" * 50)
    sys.exit(1)
