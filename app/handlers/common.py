from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.services.user_service import UserService
from app.services.wallet_service import WalletService
from app.database.session import get_db_session
from app.keyboards.inline.common import main_menu_keyboard
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    """دستور /start"""
    await state.clear()
    
    with get_db_session() as db:
        user_service = UserService(db)
        user = user_service.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            # ثبت کاربر جدید
            user = user_service.register_or_update_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code,
                is_bot=message.from_user.is_bot,
                is_premium=getattr(message.from_user, 'is_premium', False)
            )
        
        wallet_service = WalletService(db)
        wallet = wallet_service.get_wallet(user.id)
        balance = wallet.balance if wallet else 0
    
    # فرمت موجودی
    formatted_balance = f"{balance:,}".replace(',', '٬')
    
    # پیام خوش‌آمدگویی
    from datetime import datetime
    if user.created_at.date() == datetime.now().date():
        text = (
            "👋 سلام!\n"
            "به **ECHO VPN** خوش آمدید.\n\n"
            "از منوی زیر سرویس موردنظر خود را انتخاب کنید:"
        )
    else:
        text = (
            f"👋 خوش برگشتی!\n\n"
            f"💰 موجودی:\n"
            f"**{formatted_balance} تومان**\n\n"
            "چه کاری می‌خواهی انجام بدهی؟"
        )
    
    await message.answer(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    """دستور /cancel"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(
            "✅ عملیات لغو شد.\n"
            "برای شروع مجدد از منوی اصلی استفاده کنید.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await message.answer(
            "هیچ عملیات فعالی وجود ندارد.",
            reply_markup=main_menu_keyboard()
        )

@router.message(F.text == "🏠 منوی اصلی")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """بازگشت به منوی اصلی"""
    await state.clear()
    await start_command(message, state)
