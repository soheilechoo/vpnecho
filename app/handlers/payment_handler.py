from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import func
import os
import uuid
from datetime import datetime

from database.database import db
from database.models import Payment, WalletTransaction, User, TransactionType, PaymentStatus

router = Router()

class PaymentStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()

# ============================================================
# 1. شروع فرآیند پرداخت
# ============================================================

@dp.callback_query(F.data == "deposit")
async def start_payment(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند پرداخت"""
    await state.set_state(PaymentStates.waiting_for_amount)
    await callback.message.edit_text(
        "💳 **افزایش موجودی**\n\n"
        "لطفاً مبلغ مورد نظر را به تومان وارد کنید:\n\n"
        "📌 حداقل مبلغ: 1,000 تومان\n"
        "📌 حداکثر مبلغ: 10,000,000 تومان\n\n"
        "مبلغ را به تومان وارد کنید (فقط عدد):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت", callback_data="wallet")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(PaymentStates.waiting_for_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    """پردازش مبلغ پرداخت"""
    try:
        amount = int(message.text.strip())
        
        if amount < 1000:
            await message.answer("❌ حداقل مبلغ 1,000 تومان است. دوباره وارد کنید:")
            return
        
        if amount > 10000000:
            await message.answer("❌ حداکثر مبلغ 10,000,000 تومان است. دوباره وارد کنید:")
            return
        
        await state.update_data(amount=amount)
        
        # دریافت اطلاعات کارت از دیتابیس
        from database.models import BankCard
        with db.get_session() as session:
            card = session.query(BankCard).filter_by(is_active=True).first()
            if card:
                card_number = " ".join([card.card_number[i:i+4] for i in range(0, 16, 4)])
                card_owner = card.card_holder_name
            else:
                card_number = os.getenv('CARD_NUMBER', '6037-9912-3456-7890')
                card_owner = os.getenv('CARD_OWNER', 'ECHO VPN')
        
        await message.answer(
            f"💳 **اطلاعات پرداخت**\n\n"
            f"💰 مبلغ پرداخت: **{amount:,}** تومان\n\n"
            f"🏦 شماره کارت:\n`{card_number}`\n\n"
            f"👤 نام صاحب کارت:\n**{card_owner}**\n\n"
            f"⬇️ پس از واریز مبلغ، روی دکمه زیر کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📸 پرداخت کردم / ارسال رسید", callback_data="send_receipt")],
                [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_payment")]
            ]),
            parse_mode="Markdown"
        )
        await state.set_state(PaymentStates.waiting_for_receipt)
        
    except ValueError:
        await message.answer("❌ لطفاً فقط عدد وارد کنید:")

# ============================================================
# 2. ارسال رسید
# ============================================================

@dp.callback_query(F.data == "send_receipt", PaymentStates.waiting_for_receipt)
async def send_receipt_start(callback: CallbackQuery, state: FSMContext):
    """دریافت رسید از کاربر"""
    data = await state.get_data()
    amount = data.get('amount', 0)
    
    if amount == 0:
        await callback.answer("خطا! لطفاً دوباره تلاش کنید.")
        return
    
    await callback.message.edit_text(
        f"📸 **ارسال رسید پرداخت**\n\n"
        f"💰 مبلغ: {amount:,} تومان\n\n"
        "لطفاً تصویر رسید پرداخت را ارسال کنید.\n"
        "📎 می‌توانید عکس یا فایل ارسال کنید.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_payment")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(PaymentStates.waiting_for_receipt, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext):
    """پردازش رسید به صورت عکس"""
    await process_receipt(message, state, "photo", message.photo[-1].file_id)

@dp.message(PaymentStates.waiting_for_receipt, F.document)
async def process_receipt_document(message: Message, state: FSMContext):
    """پردازش رسید به صورت فایل"""
    await process_receipt(message, state, "document", message.document.file_id)

async def process_receipt(message: Message, state: FSMContext, file_type: str, file_id: str):
    """پردازش رسید و ذخیره در دیتابیس"""
    data = await state.get_data()
    amount = data.get('amount', 0)
    user = message.from_user
    
    # ایجاد شناسه یکتا برای تراکنش
    transaction_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    
    with db.get_session() as session:
        # پیدا کردن یا ایجاد کاربر
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(db_user)
            session.flush()
        
        # ایجاد پرداخت
        payment = Payment(
            transaction_id=transaction_id,
            user_id=db_user.id,
            amount=amount,
            status=PaymentStatus.PENDING,
            receipt_file_id=file_id,
            receipt_type=file_type
        )
        session.add(payment)
        session.commit()
    
    # ارسال به ادمین
    await send_payment_to_admin(message, db_user, payment, amount)
    
    await state.clear()
    await message.answer(
        "✅ **رسید شما با موفقیت دریافت شد!**\n\n"
        "⏳ در حال بررسی توسط ادمین...\n"
        "به زودی به شما اطلاع داده می‌شود.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

# ============================================================
# 3. ارسال پرداخت به ادمین
# ============================================================

async def send_payment_to_admin(message: Message, user: User, payment: Payment, amount: int):
    """ارسال اطلاعات پرداخت به ادمین"""
    admin_id = int(os.getenv('ADMIN_IDS', '0'))
    
    if admin_id == 0:
        return
    
    text = (
        f"📸 **رسید جدید**\n\n"
        f"👤 کاربر: {user.first_name or 'نامشخص'}\n"
        f"📱 یوزرنیم: @{user.username or 'ندارد'}\n"
        f"🆔 شناسه: `{user.telegram_id}`\n"
        f"💰 مبلغ: **{amount:,}** تومان\n"
        f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"🆔 شماره تراکنش: `{payment.transaction_id}`"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تایید پرداخت", callback_data=f"confirm_payment_{payment.id}"),
            InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"reject_payment_{payment.id}")
        ]
    ])
    
    try:
        if payment.receipt_type == "photo":
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=payment.receipt_file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await message.bot.send_document(
                chat_id=admin_id,
                document=payment.receipt_file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"❌ خطا در ارسال به ادمین: {e}")

# ============================================================
# 4. تأیید پرداخت توسط ادمین
# ============================================================

@dp.callback_query(F.data.startswith("confirm_payment_"))
async def confirm_payment(callback: CallbackQuery):
    """تأیید پرداخت توسط ادمین"""
    payment_id = int(callback.data.replace("confirm_payment_", ""))
    
    with db.get_session() as session:
        # پیدا کردن پرداخت
        payment = session.query(Payment).filter_by(id=payment_id).first()
        if not payment:
            await callback.answer("پرداخت یافت نشد!")
            return
        
        # بررسی وضعیت
        if payment.status == PaymentStatus.SUCCESS:
            await callback.message.edit_text(
                f"⚠️ این تراکنش قبلاً تایید شده است!\n\n"
                f"💰 مبلغ: {payment.amount:,.0f} تومان\n"
                f"🆔 شماره تراکنش: {payment.transaction_id}",
                parse_mode="Markdown"
            )
            await callback.answer("قبلاً تایید شده!")
            return
        
        if payment.status == PaymentStatus.REJECTED:
            await callback.answer("این تراکنش قبلاً رد شده است!")
            return
        
        # دریافت اطلاعات کاربر
        user = session.query(User).filter_by(id=payment.user_id).first()
        if not user:
            await callback.answer("کاربر یافت نشد!")
            return
        
        # ذخیره مقادیر قبل از تغییر
        balance_before = user.balance
        
        # افزایش موجودی
        user.balance += payment.amount
        user.successful_transactions += 1
        
        # به‌روزرسانی وضعیت پرداخت
        payment.status = PaymentStatus.SUCCESS
        payment.confirmed_at = func.now()
        payment.admin_id = callback.from_user.id
        
        # ثبت تراکنش در تاریخچه
        wallet_transaction = WalletTransaction(
            user_id=user.id,
            type=TransactionType.DEPOSIT,
            amount=payment.amount,
            balance_before=balance_before,
            balance_after=user.balance,
            reference_id=payment.transaction_id,
            description=f"شارژ حساب - تراکنش {payment.transaction_id}"
        )
        session.add(wallet_transaction)
        session.commit()
        
        # ارسال پیام موفقیت به کاربر
        try:
            await callback.bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"✅ **پرداخت تایید شد!**\n\n"
                    f"💰 مبلغ اضافه شده: **{payment.amount:,.0f}** تومان\n"
                    f"💳 موجودی فعلی: **{user.balance:,.0f}** تومان\n"
                    f"📊 تعداد تراکنش‌های موفق: {user.successful_transactions}\n"
                    f"🆔 شماره تراکنش: `{payment.transaction_id}`"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ خطا در ارسال به کاربر: {e}")
        
        # به‌روزرسانی پیام ادمین
        await callback.message.edit_text(
            f"✅ **پرداخت تایید شد**\n\n"
            f"👤 کاربر: @{user.username or 'نامشخص'}\n"
            f"💰 مبلغ: **{payment.amount:,.0f}** تومان\n"
            f"🆔 تراکنش: `{payment.transaction_id}`\n"
            f"👨‍💼 تایید شده توسط: {callback.from_user.first_name}",
            parse_mode="Markdown"
        )
        
        await callback.answer("✅ پرداخت تایید شد!")

# ============================================================
# 5. رد پرداخت توسط ادمین
# ============================================================

@dp.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: CallbackQuery):
    """رد پرداخت توسط ادمین"""
    payment_id = int(callback.data.replace("reject_payment_", ""))
    
    with db.get_session() as session:
        payment = session.query(Payment).filter_by(id=payment_id).first()
        if not payment:
            await callback.answer("پرداخت یافت نشد!")
            return
        
        if payment.status == PaymentStatus.SUCCESS:
            await callback.answer("این تراکنش قبلاً تایید شده است!")
            return
        
        if payment.status == PaymentStatus.REJECTED:
            await callback.answer("این تراکنش قبلاً رد شده است!")
            return
        
        # به‌روزرسانی وضعیت
        payment.status = PaymentStatus.REJECTED
        payment.rejected_at = func.now()
        payment.admin_id = callback.from_user.id
        
        user = session.query(User).filter_by(id=payment.user_id).first()
        session.commit()
        
        # ارسال پیام به کاربر
        try:
            await callback.bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"❌ **پرداخت شما رد شد**\n\n"
                    f"💰 مبلغ: **{payment.amount:,.0f}** تومان\n"
                    f"🆔 شماره تراکنش: `{payment.transaction_id}`\n\n"
                    f"در صورت نیاز با پشتیبانی تماس بگیرید."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ خطا در ارسال به کاربر: {e}")
        
        # به‌روزرسانی پیام ادمین
        await callback.message.edit_text(
            f"❌ **پرداخت رد شد**\n\n"
            f"👤 کاربر: @{user.username or 'نامشخص'}\n"
            f"💰 مبلغ: **{payment.amount:,.0f}** تومان\n"
            f"🆔 تراکنش: `{payment.transaction_id}`\n"
            f"👨‍💼 رد شده توسط: {callback.from_user.first_name}",
            parse_mode="Markdown"
        )
        
        await callback.answer("❌ پرداخت رد شد!")

# ============================================================
# 6. لغو پرداخت
# ============================================================

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """لغو فرآیند پرداخت"""
    await state.clear()
    await callback.message.edit_text(
        "❌ عملیات پرداخت لغو شد.",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

# ============================================================
# 7. توابع کمکی
# ============================================================

from keyboards.user_keyboards import get_main_menu_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def register_payment_handlers(dp):
    dp.include_router(router)
