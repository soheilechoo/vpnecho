from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import func
import uuid

from database.database import db
from database.models import User, Purchase, WalletTransaction, TransactionType, Product

router = Router()

# ============================================================
# 1. فرآیند خرید
# ============================================================

@dp.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: CallbackQuery):
    """پردازش خرید محصول"""
    product_type = callback.data.replace("buy_", "")
    
    product_names = {
        "vip_single": "VPN VIP تک کاربره",
        "vip_dual": "VPN VIP دو کاربره",
        "normal_single": "VPN معمولی تک کاربره",
        "normal_dual": "VPN معمولی دو کاربره"
    }
    
    with db.get_session() as session:
        # پیدا کردن کاربر
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        if not user:
            await callback.answer("لطفاً ابتدا /start را بزنید!")
            return
        
        # پیدا کردن محصول
        product = session.query(Product).filter_by(product_type=product_type).first()
        if not product:
            await callback.answer("محصول یافت نشد!")
            return
        
        # بررسی موجودی
        if user.balance < product.price:
            await callback.message.edit_text(
                f"❌ **موجودی کافی نیست!**\n\n"
                f"💳 موجودی شما: **{user.balance:,.0f}** تومان\n"
                f"💰 قیمت سرویس: **{product.price:,.0f}** تومان\n"
                f"📌 مبلغ مورد نیاز: **{product.price - user.balance:,.0f}** تومان\n\n"
                f"لطفاً ابتدا حساب خود را شارژ کنید.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💰 افزایش موجودی", callback_data="deposit")],
                    [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
                ]),
                parse_mode="Markdown"
            )
            await callback.answer()
            return
        
        # شروع تراکنش دیتابیس (Atomic)
        try:
            # ذخیره مقادیر قبل
            balance_before = user.balance
            
            # کاهش موجودی
            user.balance -= product.price
            
            # ایجاد شناسه تراکنش
            transaction_id = f"PUR-{uuid.uuid4().hex[:8].upper()}"
            
            # ثبت خرید
            purchase = Purchase(
                transaction_id=transaction_id,
                user_id=user.id,
                product_id=product.id,
                product_name=product.name,
                amount=product.price,
                status="success"
            )
            session.add(purchase)
            
            # ثبت تراکنش در تاریخچه
            wallet_transaction = WalletTransaction(
                user_id=user.id,
                type=TransactionType.PURCHASE,
                amount=-product.price,
                balance_before=balance_before,
                balance_after=user.balance,
                reference_id=transaction_id,
                description=f"خرید {product.name}"
            )
            session.add(wallet_transaction)
            
            session.commit()
            
            # ارسال پیام موفقیت
            await callback.message.edit_text(
                f"✅ **خرید با موفقیت انجام شد!**\n\n"
                f"📦 سرویس: **{product.name}**\n"
                f"💰 مبلغ: **{product.price:,.0f}** تومان\n"
                f"💳 موجودی قبل: **{balance_before:,.0f}** تومان\n"
                f"💳 موجودی بعد: **{user.balance:,.0f}** تومان\n"
                f"🆔 شماره تراکنش: `{transaction_id}`",
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            session.rollback()
            await callback.message.edit_text(
                f"❌ خطا در انجام خرید: {e}\n\n"
                f"لطفاً دوباره تلاش کنید.",
                reply_markup=get_main_menu_keyboard()
            )
            print(f"❌ خطا در خرید: {e}")
    
    await callback.answer()

# ============================================================
# 2. توابع کمکی
# ============================================================

from keyboards.user_keyboards import get_main_menu_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def register_purchase_handlers(dp):
    dp.include_router(router)
