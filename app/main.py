import sys
import os
import traceback
import asyncio
import uuid
from datetime import datetime

# ایجاد پوشه‌های لازم
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

print("=" * 50)
print("🚀 Starting VPN Bot...")
print("=" * 50)
sys.stdout.flush()

# ============================================================
# بارگذاری متغیرهای محیطی
# ============================================================

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except Exception as e:
    print(f"❌ Error loading .env: {e}")
    sys.exit(1)

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    print("❌ BOT_TOKEN not found!")
    sys.exit(1)
print("✅ BOT_TOKEN found")

ADMIN_IDS = int(os.getenv('ADMIN_IDS', '0'))
print(f"✅ ADMIN_IDS: {ADMIN_IDS}")

# ============================================================
# ایمپورت‌های اصلی
# ============================================================

try:
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.exceptions import TelegramBadRequest
    print("✅ aiogram imported")
except Exception as e:
    print(f"❌ Error importing aiogram: {e}")
    sys.exit(1)

# ============================================================
# دیتابیس
# ============================================================

try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, BigInteger, Index, Enum
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.sql import func
    from contextlib import contextmanager
    import enum
    print("✅ SQLAlchemy imported")
except Exception as e:
    print(f"❌ Error importing SQLAlchemy: {e}")
    sys.exit(1)

# ============================================================
# مدل‌های دیتابیس
# ============================================================

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/vpn_bot.db')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    REJECTED = "rejected"

class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    PURCHASE = "purchase"
    REFUND = "refund"
    ADMIN_CREDIT = "admin_credit"
    ADMIN_DEBIT = "admin_debit"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    balance = Column(Float, default=0.0)
    successful_transactions = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    receipt_file_id = Column(String(200), nullable=True)
    receipt_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    admin_id = Column(BigInteger, nullable=True)
    rejection_reason = Column(Text, nullable=True)

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    reference_id = Column(String(100), nullable=True)
    status = Column(String(20), default="success")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    product_type = Column(String(50), unique=True, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BankCard(Base):
    __tablename__ = "bank_cards"
    id = Column(Integer, primary_key=True, index=True)
    card_number = Column(String(16), unique=True, nullable=False, index=True)
    card_holder_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ProductPrice(Base):
    __tablename__ = "product_prices"
    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String(50), unique=True, nullable=False, index=True)
    price = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

# ============================================================
# ایجاد جداول
# ============================================================

Base.metadata.create_all(bind=engine)
print("✅ Database tables created")

@contextmanager
def get_db():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# ============================================================
# ایجاد ربات
# ============================================================

storage = MemoryStorage()
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=storage)

print("✅ Bot and Dispatcher created")

# ============================================================
# State‌ها
# ============================================================

class WalletState(StatesGroup):
    entering_amount = State()
    sending_receipt = State()

# ============================================================
# تابع کمکی برای ویرایش ایمن پیام
# ============================================================

async def safe_edit_text(message, text, reply_markup=None, parse_mode="Markdown"):
    """ویرایش ایمن پیام با بررسی تغییرات"""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        error_msg = str(e)
        if "message is not modified" in error_msg:
            pass
        elif "message to edit not found" in error_msg:
            await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            print(f"❌ Safe edit error: {e}")
            try:
                await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
            except:
                pass

# ============================================================
# کیبورد منوی اصلی کاربر
# ============================================================

def main_menu():
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

# ============================================================
# کیبوردهای مدیریت کیف پول
# ============================================================

def wallet_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 موجودی من", callback_data="balance")],
        [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
        [InlineKeyboardButton(text="📜 تاریخچه تراکنش‌ها", callback_data="transactions")],
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
    ])

# ============================================================
# کیبوردهای پنل ادمین
# ============================================================

def admin_menu():
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
            InlineKeyboardButton(text="💳 مدیریت شماره کارت", callback_data="admin_cards")
        ],
        [
            InlineKeyboardButton(text="📢 ارسال پیام", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="🔎 جستجوی کاربر", callback_data="admin_search")
        ],
        [
            InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="admin_settings"),
            InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")
        ]
    ])

# ============================================================
# کیبوردهای مدیریت قیمت‌ها
# ============================================================

def prices_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ ویرایش قیمت", callback_data="edit_price")],
        [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
    ])

def product_selection_menu(products):
    product_names = {
        "vip_single": "🟣 VIP تک کاربره",
        "vip_dual": "🟣 VIP دو کاربره",
        "normal_single": "🔵 معمولی تک کاربره",
        "normal_dual": "🔵 معمولی دو کاربره"
    }
    buttons = []
    for product in products:
        name = product_names.get(product.product_type, product.product_type)
        buttons.append([
            InlineKeyboardButton(
                text=f"{name} - {product.price:,.0f} تومان",
                callback_data=f"price_product_{product.product_type}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="↩️ بازگشت", callback_data="admin_prices")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ============================================================
# کیبوردهای مدیریت کارت
# ============================================================

def card_management_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن شماره کارت", callback_data="add_card")],
        [InlineKeyboardButton(text="📋 لیست شماره کارت‌ها", callback_data="list_cards")],
        [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
    ])

def cards_list_menu(cards):
    buttons = []
    for card in cards:
        formatted = " ".join([card.card_number[i:i+4] for i in range(0, 16, 4)])
        buttons.append([
            InlineKeyboardButton(
                text=f"💳 {formatted}",
                callback_data=f"view_card_{card.id}"
            )
        ])
        buttons.append([
            InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"edit_card_{card.id}"),
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"delete_card_{card.id}")
        ])
    buttons.append([InlineKeyboardButton(text="↩️ بازگشت", callback_data="admin_cards")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تایید و ذخیره", callback_data="confirm_card"),
            InlineKeyboardButton(text="❌ لغو", callback_data="cancel_card")
        ]
    ])

def back_to_cards_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="admin_cards")]
    ])

# ============================================================
# کیبوردهای پرداخت
# ============================================================

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 ارسال رسید", callback_data="send_receipt")],
        [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_payment")]
    ])

# ============================================================
# هندلرهای اصلی
# ============================================================

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user = message.from_user
    with get_db() as session:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        if not db_user:
            db_user = User(telegram_id=user.id, username=user.username, first_name=user.first_name)
            session.add(db_user)
            session.commit()
            print(f"✅ New user: {user.id}")
    await message.answer(
        f"👋 {user.first_name} عزیز به ربات فروش VPN خوش آمدید! 🌟\n\n"
        f"💰 موجودی حساب شما: 0 تومان\n\n"
        f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu()
    )

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id != ADMIN_IDS:
        await message.answer("⛔ شما دسترسی به این بخش ندارید.")
        return
    await message.answer(
        "👋 به پنل مدیریت خوش آمدید!\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_menu()
    )

# ============================================================
# هندلرهای دکمه‌ها
# ============================================================

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data
    user = callback.from_user
    
    try:
        # ======== منوی اصلی ========
        if data == "main_menu":
            await safe_edit_text(callback.message, "🏠 منوی اصلی", main_menu())
            await callback.answer()
            return
        
        # ======== کیف پول ========
        if data == "wallet":
            with get_db() as session:
                db_user = session.query(User).filter_by(telegram_id=user.id).first()
                balance = db_user.balance if db_user else 0
            await safe_edit_text(
                callback.message,
                f"💰 مدیریت کیف پول\n\n💳 موجودی فعلی: {balance:,.0f} تومان\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                wallet_menu()
            )
            await callback.answer()
            return
        
        # ======== موجودی من ========
        if data == "balance":
            with get_db() as session:
                db_user = session.query(User).filter_by(telegram_id=user.id).first()
                balance = db_user.balance if db_user else 0
                count = db_user.successful_transactions if db_user else 0
            await safe_edit_text(
                callback.message,
                f"💰 موجودی حساب شما\n\n💳 موجودی فعلی: {balance:,.0f} تومان\n📊 تعداد تراکنش‌های موفق: {count}",
                wallet_menu()
            )
            await callback.answer()
            return
        
        # ======== تاریخچه تراکنش‌ها ========
        if data == "transactions":
            with get_db() as session:
                db_user = session.query(User).filter_by(telegram_id=user.id).first()
                if db_user:
                    txs = session.query(WalletTransaction).filter_by(user_id=db_user.id).order_by(
                        WalletTransaction.created_at.desc()
                    ).limit(10).all()
                else:
                    txs = []
            
            if not txs:
                text = "📜 تاریخچه تراکنش‌ها\n\nهیچ تراکنشی یافت نشد."
            else:
                text = "📜 ۱۰ تراکنش اخیر\n\n"
                for t in txs:
                    sign = "+" if t.amount > 0 else ""
                    text += f"• {t.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    text += f"  {t.type.value}: {sign}{t.amount:,.0f} تومان\n"
                    text += f"  موجودی: {t.balance_after:,.0f} تومان\n\n"
            
            await safe_edit_text(callback.message, text, wallet_menu())
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
                "مبلغ را به تومان وارد کنید (فقط عدد):"
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
                "🔵 خرید VPN معمولی\n\nلطفاً نوع کاربری مورد نظر خود را انتخاب کنید:",
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
        
        # ======== پردازش خرید ========
        if data.startswith("buy_vip_") or data.startswith("buy_normal_"):
            product_type = data.replace("buy_", "")
            with get_db() as session:
                db_user = session.query(User).filter_by(telegram_id=user.id).first()
                if not db_user:
                    await callback.answer("لطفاً /start را بزنید!")
                    return
                
                product = session.query(Product).filter_by(product_type=product_type).first()
                if not product:
                    await callback.answer("محصول یافت نشد!")
                    return
                
                if db_user.balance < product.price:
                    await safe_edit_text(
                        callback.message,
                        f"❌ موجودی کافی نیست!\n\n"
                        f"💳 موجودی شما: {db_user.balance:,.0f} تومان\n"
                        f"💰 قیمت سرویس: {product.price:,.0f} تومان\n"
                        f"📌 مبلغ مورد نیاز: {product.price - db_user.balance:,.0f} تومان",
                        InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💰 افزایش موجودی", callback_data="deposit")],
                            [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
                        ])
                    )
                    await callback.answer()
                    return
                
                # خرید
                balance_before = db_user.balance
                db_user.balance -= product.price
                transaction_id = f"PUR-{uuid.uuid4().hex[:8].upper()}"
                
                wallet_tx = WalletTransaction(
                    user_id=db_user.id,
                    type=TransactionType.PURCHASE,
                    amount=-product.price,
                    balance_before=balance_before,
                    balance_after=db_user.balance,
                    reference_id=transaction_id,
                    description=f"خرید {product.name}"
                )
                session.add(wallet_tx)
                session.commit()
                
                await safe_edit_text(
                    callback.message,
                    f"✅ خرید با موفقیت انجام شد!\n\n"
                    f"📦 سرویس: {product.name}\n"
                    f"💰 مبلغ: {product.price:,.0f} تومان\n"
                    f"💳 موجودی قبل: {balance_before:,.0f} تومان\n"
                    f"💳 موجودی بعد: {db_user.balance:,.0f} تومان\n"
                    f"🆔 شماره تراکنش: {transaction_id}",
                    main_menu()
                )
            await callback.answer()
            return
        
        # ======== پشتیبانی ========
        if data == "support":
            await safe_edit_text(
                callback.message,
                "🎧 پشتیبانی\n\n"
                "برای ارتباط با پشتیبانی با @EchoVpnShopBot تماس بگیرید.",
                main_menu()
            )
            await callback.answer()
            return
        
        # ======== پروفایل ========
        if data == "profile":
            with get_db() as session:
                db_user = session.query(User).filter_by(telegram_id=user.id).first()
                balance = db_user.balance if db_user else 0
                count = db_user.successful_transactions if db_user else 0
            await safe_edit_text(
                callback.message,
                f"👤 پروفایل کاربری\n\n"
                f"🆔 شناسه: {user.id}\n"
                f"👤 نام: {user.first_name or 'نامشخص'}\n"
                f"📱 یوزرنیم: @{user.username or 'ندارد'}\n\n"
                f"💰 موجودی: {balance:,.0f} تومان\n"
                f"📊 تعداد تراکنش‌های موفق: {count}",
                main_menu()
            )
            await callback.answer()
            return
        
        # ======== آموزش‌ها ========
        if data == "tutorials":
            await safe_edit_text(
                callback.message,
                "🎓 آموزش‌ها\n\nهیچ آموزشی یافت نشد.",
                main_menu()
            )
            await callback.answer()
            return
        
        # ======== بازگشت به پنل ادمین ========
        if data == "back_to_admin":
            await safe_edit_text(
                callback.message,
                "👋 به پنل مدیریت خوش آمدید!\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                admin_menu()
            )
            await callback.answer()
            return
        
        # ======== پنل ادمین - آمار ========
        if data == "admin_stats":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            with get_db() as session:
                users_count = session.query(User).count()
                orders_count = session.query(Order).count()
                pending_orders = session.query(Order).filter_by(status="pending").count()
                total_revenue = session.query(Order).filter_by(status="delivered").with_entities(func.sum(Order.price)).scalar() or 0
            await safe_edit_text(
                callback.message,
                f"📊 آمار کلی\n\n"
                f"👥 کاربران: {users_count}\n"
                f"🛒 سفارش‌ها: {orders_count}\n"
                f"⏳ در انتظار: {pending_orders}\n"
                f"💰 درآمد کل: {total_revenue:,.0f} تومان",
                admin_menu()
            )
            await callback.answer()
            return
        
        # ======== پنل ادمین - کاربران ========
        if data == "admin_users":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            with get_db() as session:
                total = session.query(User).count()
                active = session.query(User).filter_by(is_active=True).count()
            await safe_edit_text(
                callback.message,
                f"👥 مدیریت کاربران\n\n"
                f"📊 تعداد کل کاربران: {total}\n"
                f"✅ کاربران فعال: {active}\n"
                f"🚫 کاربران مسدود: {total - active}\n\n"
                f"برای جستجوی کاربر از دکمه زیر استفاده کنید:",
                InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔎 جستجوی کاربر", callback_data="admin_search")],
                    [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
                ])
            )
            await callback.answer()
            return
        
        # ======== پنل ادمین - مدیریت قیمت‌ها ========
        if data == "admin_prices":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            with get_db() as session:
                prices = session.query(ProductPrice).all()
                if not prices:
                    default_prices = [
                        ("vip_single", 250),
                        ("vip_dual", 450),
                        ("normal_single", 190),
                        ("normal_dual", 270)
                    ]
                    for product_type, price in default_prices:
                        existing = session.query(ProductPrice).filter_by(product_type=product_type).first()
                        if not existing:
                            session.add(ProductPrice(product_type=product_type, price=price))
                    session.commit()
                    prices = session.query(ProductPrice).all()
                
                price_text = "📋 مدیریت قیمت‌ها\n\n"
                product_names = {
                    "vip_single": "🟣 VIP تک کاربره",
                    "vip_dual": "🟣 VIP دو کاربره",
                    "normal_single": "🔵 معمولی تک کاربره",
                    "normal_dual": "🔵 معمولی دو کاربره"
                }
                for p in prices:
                    name = product_names.get(p.product_type, p.product_type)
                    price_text += f"{name}: **{p.price:,.0f}** تومان\n"
                
                await safe_edit_text(
                    callback.message,
                    price_text,
                    prices_menu(),
                    parse_mode="Markdown"
                )
            await callback.answer()
            return
        
        # ======== ویرایش قیمت ========
        if data == "edit_price":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            with get_db() as session:
                products = session.query(ProductPrice).all()
                await safe_edit_text(
                    callback.message,
                    "📝 لطفاً سرویس مورد نظر برای تغییر قیمت را انتخاب کنید:",
                    product_selection_menu(products)
                )
                await state.set_state(AdminState.waiting_for_product_selection)
            await callback.answer()
            return
        
        # ======== انتخاب محصول برای ویرایش قیمت ========
        if data.startswith("price_product_"):
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            product_type = data.replace("price_product_", "")
            await state.update_data(product_type=product_type)
            with get_db() as session:
                product = session.query(ProductPrice).filter_by(product_type=product_type).first()
                product_names = {
                    "vip_single": "VIP تک کاربره",
                    "vip_dual": "VIP دو کاربره",
                    "normal_single": "معمولی تک کاربره",
                    "normal_dual": "معمولی دو کاربره"
                }
                name = product_names.get(product_type, product_type)
                await safe_edit_text(
                    callback.message,
                    f"💰 قیمت جدید برای **{name}** را وارد کنید:\n\n"
                    f"قیمت فعلی: **{product.price:,.0f}** تومان\n\n"
                    f"لطفاً فقط عدد وارد کنید:",
                    parse_mode="Markdown"
                )
                await state.set_state(AdminState.waiting_for_new_price)
            await callback.answer()
            return
        
        # ======== پنل ادمین - مدیریت کارت‌ها ========
        if data == "admin_cards":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            await safe_edit_text(
                callback.message,
                "💳 مدیریت شماره کارت‌ها\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                card_management_menu()
            )
            await callback.answer()
            return
        
        # ======== افزودن کارت ========
        if data == "add_card":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            await state.set_state(AdminState.waiting_for_card_number)
            await safe_edit_text(
                callback.message,
                "💳 افزودن شماره کارت جدید\n\n"
                "لطفاً شماره کارت (۱۶ رقم) را وارد کنید:\n"
                "مثال: `6037997512345678`",
                parse_mode="Markdown",
                reply_markup=back_to_cards_keyboard()
            )
            await callback.answer()
            return
        
        # ======== لیست کارت‌ها ========
        if data == "list_cards":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            with get_db() as session:
                cards = session.query(BankCard).filter_by(is_active=True).all()
                if not cards:
                    await safe_edit_text(
                        callback.message,
                        "📭 هیچ شماره کارتی ثبت نشده است.",
                        card_management_menu()
                    )
                else:
                    await safe_edit_text(
                        callback.message,
                        "📋 لیست شماره کارت‌ها:",
                        cards_list_menu(cards)
                    )
            await callback.answer()
            return
        
        # ======== پنل ادمین - جستجوی کاربر ========
        if data == "admin_search":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            await safe_edit_text(
                callback.message,
                "🔎 جستجوی کاربر\n\n"
                "لطفاً شناسه تلگرام یا یوزرنیم کاربر را وارد کنید:",
                InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="↩️ بازگشت", callback_data="back_to_admin")]
                ])
            )
            await state.set_state(AdminState.waiting_for_user_search)
            await callback.answer()
            return
        
        # ======== پنل ادمین - تنظیمات ========
        if data == "admin_settings":
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            card_number = os.getenv('CARD_NUMBER', '6037-9912-3456-7890')
            card_owner = os.getenv('CARD_OWNER', 'ECHO VPN')
            await safe_edit_text(
                callback.message,
                f"⚙️ تنظیمات\n\n"
                f"💳 شماره کارت: `{card_number}`\n"
                f"👤 صاحب کارت: {card_owner}\n\n"
                f"برای تغییر شماره کارت از بخش مدیریت شماره کارت استفاده کنید.",
                parse_mode="Markdown",
                reply_markup=admin_menu()
            )
            await callback.answer()
            return
        
        # ======== دکمه‌های placeholder ادمین ========
        if data.startswith("admin_"):
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            await safe_edit_text(
                callback.message,
                f"📋 {data.replace('admin_', '').title()}\n\nاین بخش در حال توسعه است...",
                InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
                ])
            )
            await callback.answer()
            return
        
        # ======== اگر هیچکدام ========
        await callback.answer("⏳ در حال توسعه...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        await callback.answer("خطا! لطفاً دوباره تلاش کنید.")

# ============================================================
# دریافت مبلغ (FSM)
# ============================================================

@dp.message(WalletState.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 1000:
            await message.answer("❌ حداقل 1000 تومان. دوباره وارد کنید:")
            return
        if amount > 10000000:
            await message.answer("❌ حداکثر 10,000,000 تومان. دوباره وارد کنید:")
            return
        
        await state.update_data(amount=amount)
        card_number = os.getenv('CARD_NUMBER', '6037-9912-3456-7890')
        card_owner = os.getenv('CARD_OWNER', 'ECHO VPN')
        
        await message.answer(
            f"💳 اطلاعات پرداخت\n\n"
            f"💰 مبلغ: {amount:,} تومان\n"
            f"🏦 شماره کارت: {card_number}\n"
            f"👤 صاحب کارت: {card_owner}\n\n"
            f"پس از واریز، عکس رسید را ارسال کنید.",
            reply_markup=payment_keyboard()
        )
        await state.set_state(WalletState.sending_receipt)
        
    except ValueError:
        await message.answer("❌ فقط عدد وارد کنید.")

# ============================================================
# دریافت رسید
# ============================================================

@dp.callback_query(lambda c: c.data == "send_receipt")
async def send_receipt_start(callback: types.CallbackQuery, state: FSMContext):
    await safe_edit_text(
        callback.message,
        "📸 لطفاً تصویر رسید را ارسال کنید:"
    )
    await callback.answer()

@dp.message(WalletState.sending_receipt, lambda m: m.photo is not None)
async def process_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get('amount', 0)
    user = message.from_user
    file_id = message.photo[-1].file_id
    transaction_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    
    with get_db() as session:
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
        
        if ADMIN_IDS:
            await bot.send_photo(
                ADMIN_IDS,
                file_id,
                caption=f"📸 رسید جدید\n\n"
                        f"👤 کاربر: @{user.username or 'ندارد'}\n"
                        f"🆔 شناسه: {user.id}\n"
                        f"💰 مبلغ: {amount:,} تومان\n"
                        f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ تایید پرداخت", callback_data=f"confirm_{payment.id}"),
                        InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"reject_{payment.id}")
                    ]
                ])
            )
    
    await state.clear()
    await message.answer("✅ رسید شما با موفقیت دریافت شد.\n\n⏳ در حال بررسی توسط ادمین...", reply_markup=main_menu())

# ============================================================
# تایید و رد پرداخت توسط ادمین
# ============================================================

@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery):
    payment_id = int(callback.data.replace("confirm_", ""))
    
    with get_db() as session:
        payment = session.query(Payment).filter_by(id=payment_id).first()
        if not payment:
            await callback.answer("پرداخت یافت نشد!")
            return
        
        if payment.status != PaymentStatus.PENDING:
            await callback.answer("⚠️ این تراکنش قبلاً پردازش شده است!")
            return
        
        user = session.query(User).filter_by(id=payment.user_id).first()
        if not user:
            await callback.answer("کاربر یافت نشد!")
            return
        
        # افزایش موجودی
        balance_before = user.balance
        user.balance += payment.amount
        user.successful_transactions += 1
        
        payment.status = PaymentStatus.SUCCESS
        payment.confirmed_at = func.now()
        payment.admin_id = callback.from_user.id
        
        wallet_tx = WalletTransaction(
            user_id=user.id,
            type=TransactionType.DEPOSIT,
            amount=payment.amount,
            balance_before=balance_before,
            balance_after=user.balance,
            reference_id=payment.transaction_id,
            description=f"شارژ حساب - تراکنش {payment.transaction_id}"
        )
        session.add(wallet_tx)
        session.commit()
        
        # ارسال پیام به کاربر
        try:
            await bot.send_message(
                user.telegram_id,
                f"✅ پرداخت تایید شد!\n\n"
                f"💰 مبلغ اضافه شده: {payment.amount:,.0f} تومان\n"
                f"💳 موجودی فعلی: {user.balance:,.0f} تومان\n"
                f"📊 تعداد تراکنش‌های موفق: {user.successful_transactions}"
            )
        except:
            pass
        
        # به‌روزرسانی پیام ادمین
        await safe_edit_text(
            callback.message,
            f"✅ پرداخت تایید شد\n\n"
            f"👤 کاربر: @{user.username or 'ندارد'}\n"
            f"💰 مبلغ: {payment.amount:,.0f} تومان\n"
            f"🆔 Transaction: {payment.transaction_id}\n"
            f"👨‍💼 تایید شده توسط: {callback.from_user.first_name}"
        )
        await callback.answer("✅ پرداخت تایید شد!")

@dp.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    payment_id = int(callback.data.replace("reject_", ""))
    
    with get_db() as session:
        payment = session.query(Payment).filter_by(id=payment_id).first()
        if not payment:
            await callback.answer("پرداخت یافت نشد!")
            return
        
        if payment.status != PaymentStatus.PENDING:
            await callback.answer("⚠️ این تراکنش قبلاً پردازش شده است!")
            return
        
        user = session.query(User).filter_by(id=payment.user_id).first()
        
        payment.status = PaymentStatus.REJECTED
        payment.rejected_at = func.now()
        payment.admin_id = callback.from_user.id
        session.commit()
        
        # ارسال پیام به کاربر
        try:
            await bot.send_message(
                user.telegram_id,
                f"❌ پرداخت شما رد شد.\n\n💰 مبلغ: {payment.amount:,.0f} تومان"
            )
        except:
            pass
        
        # به‌روزرسانی پیام ادمین
        await safe_edit_text(
            callback.message,
            f"❌ پرداخت رد شد\n\n"
            f"👤 کاربر: @{user.username or 'ندارد'}\n"
            f"💰 مبلغ: {payment.amount:,.0f} تومان\n"
            f"🆔 Transaction: {payment.transaction_id}\n"
            f"👨‍💼 رد شده توسط: {callback.from_user.first_name}"
        )
        await callback.answer("❌ پرداخت رد شد!")

@dp.callback_query(lambda c: c.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit_text(callback.message, "❌ عملیات لغو شد.", main_menu())
    await callback.answer()

# ============================================================
# دریافت مبلغ جدید برای ویرایش قیمت (FSM ادمین)
# ============================================================

@dp.message(AdminState.waiting_for_new_price)
async def save_new_price(message: types.Message, state: FSMContext):
    try:
        new_price = float(message.text.strip())
        if new_price < 0:
            await message.answer("❌ قیمت نمی‌تواند منفی باشد. دوباره وارد کنید:")
            return
        
        data = await state.get_data()
        product_type = data.get('product_type')
        
        with get_db() as session:
            product = session.query(ProductPrice).filter_by(product_type=product_type).first()
            if product:
                old_price = product.price
                product.price = new_price
                session.commit()
                
                product_names = {
                    "vip_single": "VIP تک کاربره",
                    "vip_dual": "VIP دو کاربره",
                    "normal_single": "معمولی تک کاربره",
                    "normal_dual": "معمولی دو کاربره"
                }
                name = product_names.get(product_type, product_type)
                
                await message.answer(
                    f"✅ قیمت **{name}** با موفقیت تغییر کرد!\n\n"
                    f"💰 قیمت قبلی: {old_price:,.0f} تومان\n"
                    f"💰 قیمت جدید: {new_price:,.0f} تومان",
                    parse_mode="Markdown"
                )
                
                await state.clear()
                # بازگشت به منوی مدیریت قیمت‌ها
                with get_db() as session2:
                    prices = session2.query(ProductPrice).all()
                    price_text = "📋 مدیریت قیمت‌ها\n\n"
                    product_names2 = {
                        "vip_single": "🟣 VIP تک کاربره",
                        "vip_dual": "🟣 VIP دو کاربره",
                        "normal_single": "🔵 معمولی تک کاربره",
                        "normal_dual": "🔵 معمولی دو کاربره"
                    }
                    for p in prices:
                        name2 = product_names2.get(p.product_type, p.product_type)
                        price_text += f"{name2}: **{p.price:,.0f}** تومان\n"
                    
                    await message.answer(
                        price_text,
                        reply_markup=prices_menu(),
                        parse_mode="Markdown"
                    )
            else:
                await message.answer("❌ محصول یافت نشد.")
                
    except ValueError:
        await message.answer("❌ لطفاً فقط عدد وارد کنید:")

# ============================================================
# جستجوی کاربر (FSM ادمین)
# ============================================================

@dp.message(AdminState.waiting_for_user_search)
async def search_user(message: types.Message, state: FSMContext):
    query = message.text.strip()
    
    with get_db() as session:
        if query.isdigit():
            user = session.query(User).filter_by(telegram_id=int(query)).first()
        else:
            user = session.query(User).filter_by(username=query.replace("@", "")).first()
        
        if user:
            await message.answer(
                f"👤 اطلاعات کاربر\n\n"
                f"🆔 شناسه: {user.telegram_id}\n"
                f"👤 نام: {user.first_name or 'نامشخص'}\n"
                f"📱 یوزرنیم: @{user.username or 'ندارد'}\n"
                f"💰 موجودی: {user.balance:,.0f} تومان\n"
                f"📊 تعداد تراکنش‌های موفق: {user.successful_transactions}\n"
                f"📅 تاریخ عضویت: {user.created_at.strftime('%Y-%m-%d %H:%M')}",
                reply_markup=admin_menu()
            )
        else:
            await message.answer("❌ کاربری با این مشخصات یافت نشد.")
        await state.clear()

# ============================================================
# پردازش شماره کارت جدید (FSM ادمین)
# ============================================================

@dp.message(AdminState.waiting_for_card_number)
async def process_card_number(message: types.Message, state: FSMContext):
    card_number = message.text.strip().replace(" ", "").replace("-", "")
    
    if not card_number.isdigit():
        await message.answer("❌ شماره کارت نامعتبر است! لطفاً فقط عدد وارد کنید:")
        return
    
    if len(card_number) != 16:
        await message.answer(f"❌ شماره کارت باید ۱۶ رقم باشد. شما {len(card_number)} رقم وارد کردید. دوباره وارد کنید:")
        return
    
    with get_db() as session:
        existing = session.query(BankCard).filter_by(card_number=card_number).first()
        if existing:
            await message.answer("❌ این شماره کارت قبلاً ثبت شده است. شماره دیگری وارد کنید:")
            return
    
    await state.update_data(card_number=card_number)
    await state.set_state(AdminState.waiting_for_card_holder)
    
    formatted = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
    await message.answer(
        f"✅ شماره کارت: `{formatted}`\n\n"
        f"👤 نام صاحب کارت را وارد کنید:",
        parse_mode="Markdown"
    )

@dp.message(AdminState.waiting_for_card_holder)
async def process_card_holder(message: types.Message, state: FSMContext):
    card_holder = message.text.strip()
    
    if len(card_holder) < 3:
        await message.answer("❌ نام صاحب کارت باید حداقل ۳ کاراکتر باشد. دوباره وارد کنید:")
        return
    
    data = await state.get_data()
    card_number = data.get('card_number')
    formatted = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
    
    await state.update_data(card_holder=card_holder)
    await state.set_state(AdminState.confirm_card)
    
    await message.answer(
        f"📋 تأیید اطلاعات کارت جدید\n\n"
        f"💳 شماره کارت: `{formatted}`\n"
        f"👤 صاحب کارت: **{card_holder}**\n\n"
        f"آیا اطلاعات صحیح است؟",
        reply_markup=confirmation_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "confirm_card")
async def save_card(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    card_number = data.get('card_number')
    card_holder = data.get('card_holder')
    formatted = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
    
    with get_db() as session:
        new_card = BankCard(
            card_number=card_number,
            card_holder_name=card_holder,
            is_active=True
        )
        session.add(new_card)
        session.commit()
        
        await safe_edit_text(
            callback.message,
            f"✅ شماره کارت با موفقیت اضافه شد!\n\n"
            f"💳 شماره کارت: `{formatted}`\n"
            f"👤 صاحب کارت: **{card_holder}**",
            parse_mode="Markdown",
            reply_markup=card_management_menu()
        )
        await state.clear()
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel_card")
async def cancel_card(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit_text(callback.message, "❌ عملیات لغو شد.", card_management_menu())
    await callback.answer()

# ============================================================
# حذف کارت
# ============================================================

@dp.callback_query(lambda c: c.data.startswith("delete_card_"))
async def delete_card(callback: types.CallbackQuery, state: FSMContext):
    card_id = int(callback.data.replace("delete_card_", ""))
    
    with get_db() as session:
        card = session.query(BankCard).filter_by(id=card_id).first()
        if not card:
            await callback.answer("کارت یافت نشد!")
            return
        
        formatted = " ".join([card.card_number[i:i+4] for i in range(0, 16, 4)])
        
        await state.update_data(card_id=card_id)
        await safe_edit_text(
            callback.message,
            f"⚠️ آیا مطمئن هستید؟\n\n"
            f"شماره کارت: `{formatted}`\n"
            f"صاحب کارت: {card.card_holder_name}\n\n"
            f"آیا می‌خواهید این شماره کارت را حذف کنید؟",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ بله، حذف شود", callback_data="confirm_delete_card"),
                    InlineKeyboardButton(text="❌ لغو", callback_data="cancel_delete_card")
                ]
            ])
        )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "confirm_delete_card")
async def confirm_delete_card(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    card_id = data.get('card_id')
    
    if not card_id:
        await callback.answer("خطا! لطفاً دوباره تلاش کنید.")
        return
    
    with get_db() as session:
        card = session.query(BankCard).filter_by(id=card_id).first()
        if card:
            card.is_active = False
            session.commit()
            formatted = " ".join([card.card_number[i:i+4] for i in range(0, 16, 4)])
            await safe_edit_text(
                callback.message,
                f"✅ شماره کارت با موفقیت حذف شد!\n\n"
                f"💳 `{formatted}`",
                parse_mode="Markdown",
                reply_markup=card_management_menu()
            )
        else:
            await safe_edit_text(callback.message, "❌ کارت یافت نشد!", card_management_menu())
        await state.clear()
    await callback.answer()

@dp.callback_query(lambda c: c.data == "cancel_delete_card")
async def cancel_delete_card(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit_text(callback.message, "❌ عملیات حذف لغو شد.", card_management_menu())
    await callback.answer()

# ============================================================
# State ادمین
# ============================================================

class AdminState(StatesGroup):
    waiting_for_product_selection = State()
    waiting_for_new_price = State()
    waiting_for_card_number = State()
    waiting_for_card_holder = State()
    confirm_card = State()
    waiting_for_user_search = State()

# ============================================================
# مقداردهی اولیه محصولات
# ============================================================

with get_db() as session:
    default_products = [
        ("vip_single", "VPN VIP تک کاربره", 250),
        ("vip_dual", "VPN VIP دو کاربره", 450),
        ("normal_single", "VPN معمولی تک کاربره", 190),
        ("normal_dual", "VPN معمولی دو کاربره", 270)
    ]
    for product_type, name, price in default_products:
        existing = session.query(Product).filter_by(product_type=product_type).first()
        if not existing:
            session.add(Product(name=name, product_type=product_type, price=price))
    session.commit()

# ============================================================
# اجرای ربات
# ============================================================

async def main():
    print("=" * 50)
    print("✅ Bot is ready! 🤖")
    print("=" * 50)
    sys.stdout.flush()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)
