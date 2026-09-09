from aiogram import Router, F
from aiogram.types import CallbackQuery
import uuid

from database import db
from database.models import User, Purchase, WalletTransaction, TransactionType, Product

router = Router()

@router.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: CallbackQuery):
    product_type = callback.data.replace("buy_", "")
    
    with db.get_session() as session:
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        if not user:
            await callback.answer("لطفاً /start را بزنید!")
            return
        
        product = session.query(Product).filter_by(product_type=product_type).first()
        if not product:
            await callback.answer("محصول یافت نشد!")
            return
        
        if user.balance < product.price:
            await callback.message.edit_text(
                f"❌ **موجودی کافی نیست!**\n\n"
                f"💳 موجودی: {user.balance:,.0f} تومان\n"
                f"💰 قیمت: {product.price:,.0f} تومان\n"
                f"📌 نیاز: {product.price - user.balance:,.0f} تومان",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💰 افزایش موجودی", callback_data="deposit")],
                    [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
                ])
            )
            await callback.answer()
            return
        
        balance_before = user.balance
        user.balance -= product.price
        transaction_id = f"PUR-{uuid.uuid4().hex[:8].upper()}"
        
        purchase = Purchase(
            transaction_id=transaction_id,
            user_id=user.id,
            product_id=product.id,
            product_name=product.name,
            amount=product.price
        )
        session.add(purchase)
        
        wallet_tx = WalletTransaction(
            user_id=user.id,
            type=TransactionType.PURCHASE,
            amount=-product.price,
            balance_before=balance_before,
            balance_after=user.balance,
            reference_id=transaction_id,
            description=f"خرید {product.name}"
        )
        session.add(wallet_tx)
        session.commit()
        
        await callback.message.edit_text(
            f"✅ **خرید موفق!**\n\n"
            f"📦 {product.name}\n"
            f"💰 {product.price:,.0f} تومان\n"
            f"💳 موجودی: {user.balance:,.0f} تومان",
            reply_markup=get_main_menu_keyboard()
        )
    await callback.answer()

def register_purchase_handlers(dp):
    dp.include_router(router)
