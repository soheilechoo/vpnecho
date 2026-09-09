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
    # ⚠️ توکن را در این قسمت قرار دهید
    # ============================================
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        print("❌ BOT_TOKEN not found in environment!")
        print("💡 Please set BOT_TOKEN in Render Environment Variables")
        sys.exit(1)
    print("✅ BOT_TOKEN found")
    
    # ============ ایمپورت‌های اصلی ============
    print("⏳ Importing aiogram...")
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.exceptions import TelegramBadRequest
    print("✅ aiogram imported")
    
    # ============ ایمپورت هندلرها ============
    print("⏳ Importing handlers...")
    from handlers.admin_panel import router as admin_router
    from handlers.payment_handler import register_payment_handlers
    from handlers.purchase_handler import register_purchase_handlers
    print("✅ Handlers imported")
    
    # ============ تعریف State‌ها ============
    
    class WalletState(StatesGroup):
        entering_amount = State()
        sending_receipt = State()
    
    # ============ ایجاد ربات ============
    
    storage = MemoryStorage()
    bot = Bot(
        token=TOKEN,
        parse_mode=ParseMode.HTML
    )
    dp = Dispatcher(storage=storage)
    print("✅ Bot and Dispatcher created")
    
    # ============ ثبت هندلرها ============
    dp.include_router(admin_router)
    register_payment_handlers(dp)
    register_purchase_handlers(dp)
    print("✅ All handlers registered")
    
    # ============ کیبوردها ============
    
    def get_main_menu_keyboard():
        """منوی اصلی"""
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
    
    def get_wallet_keyboard():
        """کیبورد مدیریت کیف پول"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 موجودی من", callback_data="balance")],
            [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
            [InlineKeyboardButton(text="📜 تاریخچه تراکنش‌ها", callback_data="transactions")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
        ])
    
    def get_back_keyboard():
        """کیبورد بازگشت"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
        ])
    
    # ============ تابع کمکی برای ویرایش ایمن پیام ============
    
    async def safe_edit_text(message, text, reply_markup=None):
        try:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except TelegramBadRequest as e:
            if "message to edit not found" in str(e):
                await message.answer(text, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                raise
    
    # ============ هندلرهای پیام ============
    
    @dp.message(Command("start"))
    async def start_command(message: types.Message):
        user = message.from_user
        
        # ثبت کاربر در دیتابیس
        from database import db
        from database.models import User
        
        with db.get_session() as session:
            existing = session.query(User).filter_by(telegram_id=user.id).first()
            if not existing:
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    balance=0,
                    successful_transactions=0
                )
                session.add(new_user)
                session.commit()
                print(f"✅ New user registered: {user.id} ({user.username})")
        
        await message.answer(
            f"👋 {user.first_name} عزیز به ربات فروش VPN خوش آمدید! 🌟\n\n"
            f"💰 موجودی حساب شما: 0 تومان\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_menu_keyboard()
        )
    
    @dp.message(Command("admin"))
    async def admin_panel_command(message: types.Message):
        """ورود به پنل ادمین"""
        admin_id = int(os.getenv('ADMIN_IDS', '0'))
        
        if message.from_user.id != admin_id:
            await message.answer("⛔ شما دسترسی به این بخش ندارید.")
            return
        
        from keyboards.admin_keyboards import get_admin_main_menu
        await message.answer(
            "👋 به پنل مدیریت خوش آمدید!\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_admin_main_menu()
        )
    
    # ============ هندلرهای دکمه‌ها ============
    
    @dp.callback_query()
    async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
        data = callback.data
        user = callback.from_user
        
        try:
            # ======== منوی اصلی ========
            if data == "main_menu":
                await safe_edit_text(
                    callback.message,
                    f"🏠 منوی اصلی\n\n👋 {user.first_name} عزیز خوش آمدید!",
                    get_main_menu_keyboard()
                )
                await callback.answer()
                return
            
            # ======== کیف پول ========
            if data == "wallet":
                from database import db
                from database.models import User
                
                with db.get_session() as session:
                    db_user = session.query(User).filter_by(telegram_id=user.id).first()
                    balance = db_user.balance if db_user else 0
                
                await safe_edit_text(
                    callback.message,
                    f"💰 **مدیریت کیف پول**\n\n"
                    f"💳 موجودی فعلی: **{balance:,.0f}** تومان\n\n"
                    f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                    get_wallet_keyboard()
                )
                await callback.answer()
                return
            
            # ======== موجودی من ========
            if data == "balance":
                from database import db
                from database.models import User
                
                with db.get_session() as session:
                    db_user = session.query(User).filter_by(telegram_id=user.id).first()
                    balance = db_user.balance if db_user else 0
                    transactions = db_user.successful_transactions if db_user else 0
                
                await safe_edit_text(
                    callback.message,
                    f"💰 **موجودی حساب شما**\n\n"
                    f"💳 موجودی فعلی: **{balance:,.0f}** تومان\n"
                    f"📊 تعداد تراکنش‌های موفق: {transactions}\n\n"
                    f"برای افزایش موجودی روی دکمه زیر کلیک کنید:",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
                        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="wallet")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== خرید VPN VIP ========
            if data == "buy_vip":
                await safe_edit_text(
                    callback.message,
                    "🟣 **خرید VPN VIP**\n\nلطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="👤 تک کاربره", callback_data="buy_vip_single"),
                            InlineKeyboardButton(text="👥 دو کاربره", callback_data="buy_vip_dual")
                        ],
                        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== خرید VPN معمولی ========
            if data == "buy_normal":
                await safe_edit_text(
                    callback.message,
                    "🔵 **خرید VPN معمولی**\n\nلطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="👤 تک کاربره", callback_data="buy_normal_single"),
                            InlineKeyboardButton(text="👥 دو کاربره", callback_data="buy_normal_dual")
                        ],
                        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== پشتیبانی ========
            if data == "support":
                await safe_edit_text(
                    callback.message,
                    "🎧 **پشتیبانی**\n\n"
                    "برای ارتباط با پشتیبانی با @EchoVpnShopBot تماس بگیرید.\n\n"
                    "📱 یوزرنیم پشتیبانی: @EchoVpnShopBot",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== پروفایل ========
            if data == "profile":
                from database import db
                from database.models import User
                
                with db.get_session() as session:
                    db_user = session.query(User).filter_by(telegram_id=user.id).first()
                    if db_user:
                        balance = db_user.balance
                        transactions = db_user.successful_transactions
                    else:
                        balance = 0
                        transactions = 0
                
                await safe_edit_text(
                    callback.message,
                    f"👤 **پروفایل کاربری**\n\n"
                    f"🆔 شناسه: `{user.id}`\n"
                    f"👤 نام: {user.first_name or 'نامشخص'}\n"
                    f"📱 یوزرنیم: @{user.username or 'ندارد'}\n\n"
                    f"💰 موجودی: **{balance:,.0f}** تومان\n"
                    f"📊 تعداد تراکنش‌های موفق: {transactions}",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== آموزش‌ها ========
            if data == "tutorials":
                await safe_edit_text(
                    callback.message,
                    "🎓 **آموزش‌ها**\n\n"
                    "هیچ آموزشی یافت نشد.",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== تاریخچه تراکنش‌ها ========
            if data == "transactions":
                from database import db
                from database.models import User, WalletTransaction
                
                with db.get_session() as session:
                    db_user = session.query(User).filter_by(telegram_id=user.id).first()
                    if db_user:
                        transactions = session.query(WalletTransaction).filter_by(user_id=db_user.id).order_by(
                            WalletTransaction.created_at.desc()
                        ).limit(10).all()
                    else:
                        transactions = []
                
                if not transactions:
                    text = "📜 **تاریخچه تراکنش‌ها**\n\nهیچ تراکنشی یافت نشد."
                else:
                    text = "📜 **۱۰ تراکنش اخیر**\n\n"
                    for t in transactions:
                        amount_str = f"+{t.amount:,.0f}" if t.amount > 0 else f"{t.amount:,.0f}"
                        text += f"• {t.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                        text += f"  {t.type.value}: {amount_str} تومان\n"
                        text += f"  موجودی: {t.balance_after:,.0f} تومان\n\n"
                
                await safe_edit_text(
                    callback.message,
                    text,
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="wallet")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== اگر هیچکدام نبود ========
            await callback.answer("⏳ در حال توسعه...")
            
        except Exception as e:
            print(f"❌ خطا در handle_callback: {e}")
            traceback.print_exc()
            await callback.answer("خطایی رخ داد، لطفاً دوباره تلاش کنید.")
    
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
