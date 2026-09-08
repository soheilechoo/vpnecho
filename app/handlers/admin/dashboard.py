from aiogram import Router, types, F
from aiogram.filters import Command
from app.filters.admin_filter import AdminFilter
from app.keyboards.inline.admin_menu import admin_dashboard_keyboard
from app.database.session import get_db_session
from app.models import User, Order, Deposit
from sqlalchemy import func
import logging

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

logger = logging.getLogger(__name__)

@router.message(Command("admin"))
async def admin_command(message: types.Message):
    """دستور /admin"""
    await show_admin_dashboard(message, None)

@router.callback_query(F.data == "admin:dashboard")
async def admin_dashboard_callback(callback: types.CallbackQuery):
    """داشبورد ادمین"""
    await callback.answer()
    await show_admin_dashboard(callback.message, callback)

async def show_admin_dashboard(message: types.Message, callback: types.CallbackQuery = None):
    """نمایش داشبورد ادمین"""
    with get_db_session() as db:
        # آمار
        total_users = db.query(User).count()
        total_orders = db.query(Order).count()
        pending_orders = db.query(Order).filter(Order.status == 'PENDING').count()
        total_revenue = db.query(func.sum(Order.price)).filter(Order.status == 'DELIVERED').scalar() or 0
        pending_deposits = db.query(Deposit).filter(Deposit.status == 'PENDING').count()
    
    text = (
        f"👑 **پنل مدیریت ECHO VPN**\n\n"
        f"📊 **آمار کلی:**\n"
        f"👥 کاربران: {total_users}\n"
        f"🛒 کل سفارشات: {total_orders}\n"
        f"⏳ سفارشات در انتظار: {pending_orders}\n"
        f"💰 درآمد کل: {total_revenue:,} تومان\n"
        f"💳 درخواست‌های شارژ: {pending_deposits}\n\n"
        f"📌 از منوی زیر مدیریت کنید:"
    )
    
    keyboard = admin_dashboard_keyboard()
    
    if callback:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
