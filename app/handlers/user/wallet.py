from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import os

from states.user_states import WalletState
from keyboards.user_keyboards import get_main_menu_keyboard, get_wallet_keyboard

router = Router()

# ============ شروع فرآیند افزایش موجودی ============

@router.callback_query(F.data == "deposit")
async def deposit_start(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند افزایش موجودی"""
    
    # تنظیم حالت وارد کردن مبلغ
    await state.set_state(WalletState.entering_amount)
    
    await callback.message.edit_text(
        "💳 افزایش موجودی\n\n"
        "لطفاً مبلغ مورد نظر را به تومان وارد کنید:\n\n"
        "📌 حداقل مبلغ: 1,000 تومان\n"
        "📌 حداکثر مبلغ: 10,000,000 تومان\n\n"
        "مبلغ را به تومان وارد کنید (فقط عدد):",
        reply_markup=get_back_to_wallet_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_wallet")
async def back_to_wallet(callback: CallbackQuery, state: FSMContext):
    """بازگشت به منوی کیف پول"""
    await state.clear()
    await callback.message.edit_text(
        "💰 مدیریت کیف پول\n\n"
        "💳 موجودی فعلی: 0 تومان\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_wallet_keyboard()
    )
    await callback.answer()

def get_back_to_wallet_keyboard():
    """کیبورد بازگشت به کیف پول"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="back_to_wallet")]
    ])

# ============ دریافت مبلغ ============

@router.message(WalletState.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    """پردازش مبلغ وارد شده توسط کاربر"""
    
    try:
        # تبدیل مبلغ به عدد
        amount = int(message.text.strip())
        
        # اعتبارسنجی مبلغ
        if amount < 1000:
            await message.answer(
                "❌ حداقل مبلغ 1,000 تومان است.\n"
                "لطفاً دوباره وارد کنید:"
            )
            return
        
        if amount > 10000000:
            await message.answer(
                "❌ حداکثر مبلغ 10,000,000 تومان است.\n"
                "لطفاً دوباره وارد کنید:"
            )
            return
        
        # ذخیره مبلغ در state
        await state.update_data(amount=amount)
        
        # دریافت اطلاعات کارت از تنظیمات
        card_number = os.getenv('CARD_NUMBER', '6037-9912-3456-7890')
        card_owner = os.getenv('CARD_OWNER', 'ECHO VPN')
        
        # نمایش اطلاعات پرداخت
        await message.answer(
            f"💳 اطلاعات پرداخت\n\n"
            f"💰 مبلغ پرداخت: {amount:,} تومان\n\n"
            f"🏦 شماره کارت:\n"
            f"<code>{card_number}</code>\n\n"
            f"👤 نام صاحب کارت:\n"
            f"{card_owner}\n\n"
            f"⬇️ پس از واریز مبلغ، روی دکمه زیر کلیک کنید:",
            reply_markup=get_receipt_keyboard(),
            parse_mode="HTML"
        )
        
        # تغییر حالت به انتظار رسید
        await state.set_state(WalletState.sending_receipt)
        
    except ValueError:
        await message.answer(
            "❌ لطفاً فقط عدد وارد کنید.\n"
            "مبلغ را به تومان وارد کنید (فقط عدد):"
        )

def get_receipt_keyboard():
    """کیبورد ارسال رسید"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 پرداخت کردم / ارسال رسید", callback_data="send_receipt")],
        [InlineKeyboardButton(text="↩️ انصراف", callback_data="cancel_deposit")]
    ])

# ============ ارسال رسید ============

@router.callback_query(F.data == "send_receipt")
async def send_receipt_start(callback: CallbackQuery, state: FSMContext):
    """دریافت رسید از کاربر"""
    
    data = await state.get_data()
    amount = data.get('amount', 0)
    
    if amount == 0:
        await callback.answer("خطا در اطلاعات، لطفاً دوباره تلاش کنید.")
        return
    
    await callback.message.edit_text(
        "📸 ارسال رسید پرداخت\n\n"
        f"💰 مبلغ: {amount:,} تومان\n\n"
        "لطفاً تصویر رسید پرداخت را ارسال کنید.\n"
        "📎 می‌توانید عکس یا فایل ارسال کنید.",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_deposit")
async def cancel_deposit(callback: CallbackQuery, state: FSMContext):
    """لغو فرآیند افزایش موجودی"""
    await state.clear()
    await callback.message.edit_text(
        "❌ عملیات لغو شد.",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

def get_cancel_keyboard():
    """کیبورد لغو"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_deposit")]
    ])

# ============ دریافت رسید ============

@router.message(WalletState.sending_receipt, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext):
    """پردازش رسید به صورت عکس"""
    
    data = await state.get_data()
    amount = data.get('amount', 0)
    
    # دریافت اطلاعات عکس
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # ذخیره اطلاعات رسید
    await state.update_data(receipt_file_id=file_id, receipt_type="photo")
    
    # ارسال به ادمین
    await send_receipt_to_admin(message, state, amount, file_id, "photo")
    
    # پاک کردن state
    await state.clear()
    
    await message.answer(
        "✅ رسید شما با موفقیت دریافت شد.\n\n"
        "⏳ در حال بررسی توسط ادمین...\n"
        "به زودی به شما اطلاع داده می‌شود.",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(WalletState.sending_receipt, F.document)
async def process_receipt_document(message: Message, state: FSMContext):
    """پردازش رسید به صورت فایل"""
    
    data = await state.get_data()
    amount = data.get('amount', 0)
    
    # دریافت اطلاعات فایل
    document = message.document
    file_id = document.file_id
    
    # ذخیره اطلاعات رسید
    await state.update_data(receipt_file_id=file_id, receipt_type="document")
    
    # ارسال به ادمین
    await send_receipt_to_admin(message, state, amount, file_id, "document")
    
    # پاک کردن state
    await state.clear()
    
    await message.answer(
        "✅ رسید شما با موفقیت دریافت شد.\n\n"
        "⏳ در حال بررسی توسط ادمین...\n"
        "به زودی به شما اطلاع داده می‌شود.",
        reply_markup=get_main_menu_keyboard()
    )

# ============ ارسال رسید به ادمین ============

async def send_receipt_to_admin(message: Message, state: FSMContext, amount: int, file_id: str, file_type: str):
    """ارسال رسید به ادمین"""
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    admin_id = int(os.getenv('ADMIN_IDS', '233915651'))
    user = message.from_user
    
    # اطلاعات رسید
    receipt_info = (
        f"📸 رسید جدید\n\n"
        f"👤 کاربر: {user.first_name or 'نامشخص'}\n"
        f"📱 یوزرنیم: @{user.username or 'ندارد'}\n"
        f"🆔 شناسه: {user.id}\n"
        f"💰 مبلغ: {amount:,} تومان\n"
        f"📅 تاریخ: {message.date.strftime('%Y-%m-%d %H:%M')}\n"
        f"📎 نوع رسید: {file_type}"
    )
    
    # دکمه‌های تأیید و رد
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data=f"approve_deposit_{user.id}_{amount}"),
            InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"reject_deposit_{user.id}_{amount}")
        ]
    ])
    
    try:
        # ارسال رسید به ادمین
        if file_type == "photo":
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=receipt_info,
                reply_markup=keyboard
            )
        else:
            await message.bot.send_document(
                chat_id=admin_id,
                document=file_id,
                caption=receipt_info,
                reply_markup=keyboard
            )
        
        print(f"✅ رسید به ادمین ارسال شد: {user.id} - {amount} تومان")
        
    except Exception as e:
        print(f"❌ خطا در ارسال رسید به ادمین: {e}")
