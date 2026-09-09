from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import os
import uuid
from datetime import datetime

from database import db
from database.models import User, Payment, WalletTransaction, TransactionType, PaymentStatus
from states.user_states import WalletState
from keyboards.user_keyboards import get_main_menu_keyboard

router = Router()

@router.callback_query(F.data == "deposit")
async def start_payment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(WalletState.entering_amount)
    await callback.message.edit_text(
        "💳 **افزایش موجودی**\n\n"
        "لطفاً مبلغ مورد نظر را به تومان وارد کنید:\n\n"
        "📌 حداقل مبلغ: 1,000 تومان\n"
        "📌 حداکثر مبلغ: 10,000,000 تومان\n\n"
        "مبلغ را به تومان وارد کنید (فقط عدد):"
    )
    await callback.answer()

@router.message(WalletState.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 1000 or amount > 10000000:
            await message.answer("❌ مبلغ نامعتبر. دوباره وارد کنید:")
            return
        
        await state.update_data(amount=amount)
        card_number = os.getenv('CARD_NUMBER', '6037-9912-3456-7890')
        card_owner = os.getenv('CARD_OWNER', 'ECHO VPN')
        
        await message.answer(
            f"💳 **اطلاعات پرداخت**\n\n"
            f"💰 مبلغ: **{amount:,}** تومان\n"
            f"🏦 شماره کارت: `{card_number}`\n"
            f"👤 صاحب کارت: {card_owner}\n\n"
            f"پس از واریز، روی دکمه زیر کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📸 پرداخت کردم", callback_data="send_receipt")],
                [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_payment")]
            ])
        )
        await state.set_state(WalletState.sending_receipt)
    except ValueError:
        await message.answer("❌ فقط عدد وارد کنید.")

@router.callback_query(F.data == "send_receipt", WalletState.sending_receipt)
async def send_receipt_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount', 0)
    if amount == 0:
        await callback.answer("خطا! دوباره تلاش کنید.")
        return
    
    await callback.message.edit_text(
        f"📸 **ارسال رسید**\n\n"
        f"💰 مبلغ: {amount:,} تومان\n\n"
        "لطفاً تصویر رسید را ارسال کنید."
    )
    await callback.answer()

@router.message(WalletState.sending_receipt, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount', 0)
    user = message.from_user
    file_id = message.photo[-1].file_id
    transaction_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    
    with db.get_session() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        if not db_user:
            db_user = User(telegram_id=user.id, username=user.username, first_name=user.first_name)
            session.add(db_user)
            session.flush()
        
        payment = Payment(
            transaction_id=transaction_id,
            user_id=db_user.id,
            amount=amount,
            status=PaymentStatus.PENDING,
            receipt_file_id=file_id,
            receipt_type="photo"
        )
        session.add(payment)
        session.commit()
    
    # ارسال به ادمین
    admin_id = int(os.getenv('ADMIN_IDS', '0'))
    if admin_id:
        await message.bot.send_photo(
            admin_id,
            file_id,
            caption=f"📸 **رسید جدید**\n\n"
                    f"👤 کاربر: @{user.username or 'ندارد'}\n"
                    f"💰 مبلغ: {amount:,} تومان\n"
                    f"🆔 تراکنش: `{transaction_id}`",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ تایید", callback_data=f"confirm_payment_{payment.id}"),
                    InlineKeyboardButton(text="❌ رد", callback_data=f"reject_payment_{payment.id}")
                ]
            ])
        )
    
    await state.clear()
    await message.answer("✅ رسید دریافت شد. در حال بررسی...", reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ لغو شد.", reply_markup=get_main_menu_keyboard())
    await callback.answer()

def register_payment_handlers(dp):
    dp.include_router(router)
