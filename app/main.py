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
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.exceptions import TelegramBadRequest
    
    print("✅ aiogram imported")
    
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
    
    # ============ کیبوردها ============
    
    def get_main_menu_keyboard():
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
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 موجودی من", callback_data="balance")],
            [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
            [InlineKeyboardButton(text="📜 تاریخچه تراکنش‌ها", callback_data="transactions")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
        ])
    
    def get_back_to_wallet_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت", callback_data="back_to_wallet")]
        ])
    
    def get_receipt_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 پرداخت کردم / ارسال رسید", callback_data="send_receipt")],
            [InlineKeyboardButton(text="↩️ انصراف", callback_data="cancel_deposit")]
        ])
    
    def get_cancel_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_deposit")]
        ])
    
    def get_back_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
        ])
    
    def get_admin_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 آمار", callback_data="admin_stats"),
                InlineKeyboardButton(text="👥 کاربران", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton(text="🛒 سفارش‌ها", callback_data="admin_orders"),
                InlineKeyboardButton(text="💰 کیف پول‌ها", callback_data="admin_wallets")
            ],
            [
                InlineKeyboardButton(text="💳 پرداخت‌ها", callback_data="admin_payments"),
                InlineKeyboardButton(text="🎓 آموزش‌ها", callback_data="admin_tutorials")
            ],
            [
                InlineKeyboardButton(text="💵 مدیریت قیمت‌ها", callback_data="admin_prices"),
                InlineKeyboardButton(text="📢 ارسال پیام", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="🔎 جستجوی کاربر", callback_data="admin_search"),
                InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="admin_settings")
            ],
            [
                InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")
            ]
        ])
    
    # ============ تابع کمکی برای ویرایش ایمن پیام ============
    
    async def safe_edit_text(message, text, reply_markup=None):
        try:
            await message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest as e:
            if "message to edit not found" in str(e):
                await message.answer(text, reply_markup=reply_markup)
            else:
                raise
    
    # ============ هندلرهای پیام ============
    
    @dp.message(Command("start"))
    async def start_command(message: types.Message):
        user = message.from_user
        await message.answer(
            f"👋 {user.first_name} عزیز به ربات فروش VPN خوش آمدید! 🌟\n\n"
            f"💰 موجودی حساب شما: 0 تومان\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_menu_keyboard()
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
    
    @dp.message(Command("admin"))
    async def admin_panel(message: types.Message):
        admin_id = int(os.getenv('ADMIN_IDS', '0'))
        
        if message.from_user.id != admin_id:
            await message.answer("⛔ شما دسترسی به این بخش ندارید.")
            return
        
        await message.answer(
            "👋 به پنل مدیریت خوش آمدید!\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_admin_keyboard()
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
            
            # ======== خرید VPN VIP ========
            if data == "buy_vip":
                await safe_edit_text(
                    callback.message,
                    "🟣 خرید VPN VIP\n\nلطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="👤 تک کاربره", callback_data="vip_single"),
                            InlineKeyboardButton(text="👥 دو کاربره", callback_data="vip_dual")
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
                    "🔵 خرید VPN معمولی\n\nلطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="👤 تک کاربره", callback_data="normal_single"),
                            InlineKeyboardButton(text="👥 دو کاربره", callback_data="normal_dual")
                        ],
                        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== انتخاب محصول ========
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
                
                await safe_edit_text(
                    callback.message,
                    f"📋 تأیید خرید\n\n"
                    f"🛒 محصول: {product_names[data]}\n"
                    f"💰 قیمت: {prices[data]:,} تومان\n"
                    f"💳 موجودی فعلی: 0 تومان\n"
                    f"❌ موجودی کافی نیست!\n\n"
                    f"لطفاً ابتدا حساب خود را شارژ کنید.",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="💰 افزایش موجودی", callback_data="deposit")],
                        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== کیف پول ========
            if data == "wallet":
                await safe_edit_text(
                    callback.message,
                    "💰 مدیریت کیف پول\n\n💳 موجودی فعلی: 0 تومان\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                    get_wallet_keyboard()
                )
                await callback.answer()
                return
            
            # ======== موجودی من ========
            if data == "balance":
                await safe_edit_text(
                    callback.message,
                    "💰 موجودی حساب شما\n\n💳 موجودی فعلی: 0 تومان\n\nبرای افزایش موجودی روی دکمه زیر کلیک کنید:",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
                        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="wallet")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== تاریخچه تراکنش‌ها ========
            if data == "transactions":
                await safe_edit_text(
                    callback.message,
                    "📜 تاریخچه تراکنش‌ها\n\nهیچ تراکنشی یافت نشد.",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="wallet")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== افزایش موجودی ========
            if data == "deposit":
                await state.set_state(WalletState.entering_amount)
                
                await safe_edit_text(
                    callback.message,
                    "💳 افزایش موجودی\n\n"
                    "لطفاً مبلغ مورد نظر را به تومان وارد کنید:\n\n"
                    "📌 حداقل مبلغ: 1,000 تومان\n"
                    "📌 حداکثر مبلغ: 10,000,000 تومان\n\n"
                    "مبلغ را به تومان وارد کنید (فقط عدد):",
                    get_back_to_wallet_keyboard()
                )
                await callback.answer()
                return
            
            # ======== بازگشت به کیف پول ========
            if data == "back_to_wallet":
                await state.clear()
                await safe_edit_text(
                    callback.message,
                    "💰 مدیریت کیف پول\n\n💳 موجودی فعلی: 0 تومان\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                    get_wallet_keyboard()
                )
                await callback.answer()
                return
            
            # ======== ارسال رسید ========
            if data == "send_receipt":
                state_data = await state.get_data()
                amount = state_data.get('amount', 0)
                
                if amount == 0:
                    await callback.answer("خطا در اطلاعات، لطفاً دوباره تلاش کنید.")
                    return
                
                await safe_edit_text(
                    callback.message,
                    "📸 ارسال رسید پرداخت\n\n"
                    f"💰 مبلغ: {amount:,} تومان\n\n"
                    "لطفاً تصویر رسید پرداخت را ارسال کنید.\n"
                    "📎 می‌توانید عکس یا فایل ارسال کنید.",
                    get_cancel_keyboard()
                )
                await state.set_state(WalletState.sending_receipt)
                await callback.answer()
                return
            
            # ======== لغو افزایش موجودی ========
            if data == "cancel_deposit":
                await state.clear()
                await safe_edit_text(
                    callback.message,
                    "❌ عملیات لغو شد.",
                    get_main_menu_keyboard()
                )
                await callback.answer()
                return
            
            # ======== پشتیبانی ========
            if data == "support":
                await safe_edit_text(
                    callback.message,
                    "🎧 پشتیبانی\n\nبرای ارتباط با پشتیبانی با @EchoVpnShopBot تماس بگیرید.",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== پروفایل ========
            if data == "profile":
                await safe_edit_text(
                    callback.message,
                    f"👤 پروفایل کاربری\n\n"
                    f"🆔 شناسه: {user.id}\n"
                    f"👤 نام: {user.first_name or 'نامشخص'}\n"
                    f"📱 یوزرنیم: @{user.username or 'ندارد'}\n\n"
                    f"💰 موجودی: 0 تومان\n"
                    f"📊 تعداد سفارش‌ها: 0",
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
                    "🎓 آموزش‌ها\n\nهیچ آموزشی یافت نشد.",
                    InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
                    ])
                )
                await callback.answer()
                return
            
            # ======== پنل ادمین ========
            admin_id = int(os.getenv('ADMIN_IDS', '0'))
            
            if data.startswith("admin_") or data == "back_to_admin":
                if user.id != admin_id:
                    await callback.answer("⛔ شما دسترسی به این بخش ندارید.", show_alert=True)
                    return
                
                if data == "back_to_admin":
                    await safe_edit_text(
                        callback.message,
                        "👋 به پنل مدیریت خوش آمدید!\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                        get_admin_keyboard()
                    )
                else:
                    await safe_edit_text(
                        callback.message,
                        f"📋 {data.replace('admin_', '').title()}\n\nاین بخش در حال توسعه است...",
                        InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
                        ])
                    )
                await callback.answer()
                return
            
            # ======== اگر هیچکدام نبود ========
            await callback.answer("⏳ در حال توسعه...")
            
        except Exception as e:
            print(f"❌ خطا در handle_callback: {e}")
            await callback.answer("خطایی رخ داد، لطفاً دوباره تلاش کنید.")
    
    # ============ دریافت مبلغ (FSM) ============
    
    @dp.message(WalletState.entering_amount)
    async def process_amount(message: types.Message, state: FSMContext):
        try:
            amount = int(message.text.strip())
            
            if amount < 1000:
                await message.answer("❌ حداقل مبلغ 1,000 تومان است.\nلطفاً دوباره وارد کنید:")
                return
            
            if amount > 10000000:
                await message.answer("❌ حداکثر مبلغ 10,000,000 تومان است.\nلطفاً دوباره وارد کنید:")
                return
            
            await state.update_data(amount=amount)
            
            card_number = os.getenv('CARD_NUMBER', '6037-9912-3456-7890')
            card_owner = os.getenv('CARD_OWNER', 'ECHO VPN')
            
            await message.answer(
                f"💳 اطلاعات پرداخت\n\n"
                f"💰 مبلغ پرداخت: {amount:,} تومان\n\n"
                f"🏦 شماره کارت:\n<code>{card_number}</code>\n\n"
                f"👤 نام صاحب کارت:\n{card_owner}\n\n"
                f"⬇️ پس از واریز مبلغ، روی دکمه زیر کلیک کنید:",
                reply_markup=get_receipt_keyboard(),
                parse_mode="HTML"
            )
            
            await state.set_state(WalletState.sending_receipt)
            
        except ValueError:
            await message.answer("❌ لطفاً فقط عدد وارد کنید.\nمبلغ را به تومان وارد کنید (فقط عدد):")
    
    # ============ دریافت رسید (FSM) - اصلاح شده بدون F ============
    
    @dp.message(WalletState.sending_receipt, lambda message: message.photo is not None)
    async def process_receipt_photo(message: types.Message, state: FSMContext):
        data = await state.get_data()
        amount = data.get('amount', 0)
        photo = message.photo[-1]
        file_id = photo.file_id
        
        await send_receipt_to_admin(message, amount, file_id, "photo")
        await state.clear()
        
        await message.answer(
            "✅ رسید شما با موفقیت دریافت شد.\n\n"
            "⏳ در حال بررسی توسط ادمین...\n"
            "به زودی به شما اطلاع داده می‌شود.",
            reply_markup=get_main_menu_keyboard()
        )
    
    @dp.message(WalletState.sending_receipt, lambda message: message.document is not None)
    async def process_receipt_document(message: types.Message, state: FSMContext):
        data = await state.get_data()
        amount = data.get('amount', 0)
        document = message.document
        file_id = document.file_id
        
        await send_receipt_to_admin(message, amount, file_id, "document")
        await state.clear()
        
        await message.answer(
            "✅ رسید شما با موفقیت دریافت شد.\n\n"
            "⏳ در حال بررسی توسط ادمین...\n"
            "به زودی به شما اطلاع داده می‌شود.",
            reply_markup=get_main_menu_keyboard()
        )
    
    @dp.message(WalletState.sending_receipt)
    async def invalid_receipt(message: types.Message, state: FSMContext):
        await message.answer(
            "❌ لطفاً یک عکس یا فایل ارسال کنید.\n\n"
            "📸 برای ارسال رسید، روی دکمه زیر کلیک کنید:",
            reply_markup=get_receipt_keyboard()
        )
    
    # ============ ارسال رسید به ادمین ============
    
    async def send_receipt_to_admin(message: types.Message, amount: int, file_id: str, file_type: str):
        admin_id = int(os.getenv('ADMIN_IDS', '0'))
        user = message.from_user
        
        if admin_id == 0:
            print("⚠️ ADMIN_IDS not set!")
            return
        
        receipt_info = (
            f"📸 رسید جدید\n\n"
            f"👤 کاربر: {user.first_name or 'نامشخص'}\n"
            f"📱 یوزرنیم: @{user.username or 'ندارد'}\n"
            f"🆔 شناسه: <code>{user.id}</code>\n"
            f"💰 مبلغ: {amount:,} تومان\n"
            f"📅 تاریخ: {message.date.strftime('%Y-%m-%d %H:%M')}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data=f"approve_{user.id}_{amount}"),
                InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"reject_{user.id}_{amount}")
            ]
        ])
        
        try:
            if file_type == "photo":
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=receipt_info,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await bot.send_document(
                    chat_id=admin_id,
                    document=file_id,
                    caption=receipt_info,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            
            print(f"✅ رسید به ادمین ارسال شد: {user.id} - {amount} تومان")
            
        except Exception as e:
            print(f"❌ خطا در ارسال رسید به ادمین: {e}")
    
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
