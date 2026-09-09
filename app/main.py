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
# کیبوردها
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
            InlineKeyboardButton(text="💰 موجودی", callback_data="wallet"),
            InlineKeyboardButton(text="🎧 پشتیبانی", callback_data="support")
        ],
        [
            InlineKeyboardButton(text="👤 پروفایل", callback_data="profile")
        ]
    ])

def wallet_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 موجودی من", callback_data="balance")],
        [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
        [InlineKeyboardButton(text="📜 تاریخچه", callback_data="transactions")],
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 آمار", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 کاربران", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="💵 قیمت‌ها", callback_data="admin_prices"),
            InlineKeyboardButton(text="💳 کارت‌ها", callback_data="admin_cards")
        ],
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
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
        f"👋 {user.first_name} عزیز خوش آمدید!\n💰 موجودی: 0 تومان",
        reply_markup=main_menu()
    )

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id != ADMIN_IDS:
        await message.answer("⛔ دسترسی ندارید.")
        return
    await message.answer("👋 پنل مدیریت", reply_markup=admin_menu())

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
                f"💰 موجودی: {balance:,.0f} تومان",
                wallet_menu()
            )
            await callback.answer()
            return
        
        # ======== موجودی ========
        if data == "balance":
            with get_db() as session:
                db_user = session.query(User).filter_by(telegram_id=user.id).first()
                balance = db_user.balance if db_user else 0
                count = db_user.successful_transactions if db_user else 0
            await safe_edit_text(
                callback.message,
                f"💰 موجودی: {balance:,.0f} تومان\n📊 تراکنش‌ها: {count}",
                wallet_menu()
            )
            await callback.answer()
            return
        
        # ======== افزایش موجودی ========
        if data == "deposit":
            await state.set_state(WalletState.entering_amount)
            await safe_edit_text(
                callback.message,
                "💳 مبلغ را به تومان وارد کنید (حداقل 1000):"
            )
            await callback.answer()
            return
        
        # ======== خرید ========
        if data in ["buy_vip", "buy_normal"]:
            product_type = "vip" if data == "buy_vip" else "normal"
            await safe_edit_text(
                callback.message,
                f"🛒 خرید VPN {product_type.upper()}\nنوع کاربری را انتخاب کنید:",
                InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="👤 تک کاربره", callback_data=f"buy_{product_type}_single"),
                        InlineKeyboardButton(text="👥 دو کاربره", callback_data=f"buy_{product_type}_dual")
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
                        f"❌ موجودی کافی نیست!\n💰 موجودی: {db_user.balance:,.0f}\n💰 قیمت: {product.price:,.0f}",
                        main_menu()
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
                    f"✅ خرید موفق!\n📦 {product.name}\n💰 {product.price:,.0f} تومان\n💳 موجودی: {db_user.balance:,.0f}",
                    main_menu()
                )
            await callback.answer()
            return
        
        # ======== پشتیبانی ========
        if data == "support":
            await safe_edit_text(
                callback.message,
                "🎧 پشتیبانی: @EchoVpnShopBot",
                main_menu()
            )
            await callback.answer()
            return
        
        # ======== پروفایل ========
        if data == "profile":
            with get_db() as session:
                db_user = session.query(User).filter_by(telegram_id=user.id).first()
                balance = db_user.balance if db_user else 0
            await safe_edit_text(
                callback.message,
                f"👤 پروفایل\n🆔 {user.id}\n👤 {user.first_name}\n💰 {balance:,.0f} تومان",
                main_menu()
            )
            await callback.answer()
            return
        
        # ======== تاریخچه ========
        if data == "transactions":
            with get_db() as session:
                db_user = session.query(User).filter_by(telegram_id=user.id).first()
                if db_user:
                    txs = session.query(WalletTransaction).filter_by(user_id=db_user.id).order_by(
                        WalletTransaction.created_at.desc()
                    ).limit(5).all()
                else:
                    txs = []
            
            if not txs:
                text = "📜 هیچ تراکنشی یافت نشد."
            else:
                text = "📜 ۵ تراکنش اخیر:\n\n"
                for t in txs:
                    sign = "+" if t.amount > 0 else ""
                    text += f"{t.created_at.strftime('%H:%M')} {t.type.value}: {sign}{t.amount:,.0f} تومان\n"
            
            await safe_edit_text(callback.message, text, wallet_menu())
            await callback.answer()
            return
        
        # ======== پنل ادمین ========
        if data.startswith("admin_"):
            if user.id != ADMIN_IDS:
                await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
                return
            
            if data == "admin_stats":
                with get_db() as session:
                    users_count = session.query(User).count()
                    orders_count = session.query(Order).count()
                await safe_edit_text(
                    callback.message,
                    f"📊 آمار\n👥 کاربران: {users_count}\n🛒 سفارش‌ها: {orders_count}",
                    admin_menu()
                )
                await callback.answer()
                return
            
            if data == "admin_users":
                with get_db() as session:
                    users = session.query(User).all()
                    text = "👥 کاربران:\n\n"
                    for u in users[:10]:
                        text += f"🆔 {u.telegram_id} | @{u.username or 'ندارد'} | {u.balance:,.0f} تومان\n"
                await safe_edit_text(callback.message, text, admin_menu())
                await callback.answer()
                return
            
            if data == "admin_prices":
                with get_db() as session:
                    products = session.query(Product).all()
                    text = "💵 قیمت‌ها:\n\n"
                    for p in products:
                        text += f"{p.name}: {p.price:,.0f} تومان\n"
                await safe_edit_text(callback.message, text, admin_menu())
                await callback.answer()
                return
            
            if data == "admin_cards":
                with get_db() as session:
                    cards = session.query(BankCard).filter_by(is_active=True).all()
                    if not cards:
                        text = "💳 هیچ کارتی ثبت نشده."
                    else:
                        text = "💳 کارت‌ها:\n\n"
                        for c in cards:
                            formatted = " ".join([c.card_number[i:i+4] for i in range(0, 16, 4)])
                            text += f"{formatted}\n{c.card_holder_name}\n\n"
                await safe_edit_text(callback.message, text, admin_menu())
                await callback.answer()
                return
            
            await callback.answer("در حال توسعه...")
            return
        
        # ======== آموزش ========
        if data == "tutorials":
            await safe_edit_text(
                callback.message,
                "🎓 آموزشی موجود نیست.",
                main_menu()
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
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📸 ارسال رسید", callback_data="send_receipt")],
                [InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_payment")]
            ])
        )
        await state.set_state(WalletState.sending_receipt)
        
    except ValueError:
        await message.answer("❌ فقط عدد وارد کنید.")

# ============================================================
# دریافت رسید
# ============================================================

@dp.callback_query(lambda c: c.data == "send_receipt")
async def send_receipt_start(callback: types.CallbackQuery, state: FSMContext):
    await safe_edit_text(callback.message, "📸 لطفاً تصویر رسید را ارسال کنید:")
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
                caption=f"📸 رسید جدید\n"
                        f"👤 @{user.username or 'ندارد'}\n"
                        f"💰 {amount:,} تومان\n"
                        f"🆔 {transaction_id}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ تایید", callback_data=f"confirm_{payment.id}"),
                        InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{payment.id}")
                    ]
                ])
            )
    
    await state.clear()
    await message.answer("✅ رسید دریافت شد. در حال بررسی...", reply_markup=main_menu())

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
            await callback.answer("این پرداخت قبلاً پردازش شده!")
            return
        
        user = session.query(User).filter_by(id=payment.user_id).first()
        if not user:
            await callback.answer("کاربر یافت نشد!")
            return
        
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
            description=f"شارژ حساب"
        )
        session.add(wallet_tx)
        session.commit()
        
        try:
            await bot.send_message(
                user.telegram_id,
                f"✅ پرداخت تایید شد!\n💰 {payment.amount:,.0f} تومان اضافه شد.\n💳 موجودی: {user.balance:,.0f} تومان"
            )
        except:
            pass
        
        await safe_edit_text(
            callback.message,
            f"✅ پرداخت تایید شد!\n"
            f"👤 @{user.username or 'ندارد'}\n"
            f"💰 {payment.amount:,.0f} تومان"
        )
        await callback.answer("✅ تایید شد!")

@dp.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    payment_id = int(callback.data.replace("reject_", ""))
    
    with get_db() as session:
        payment = session.query(Payment).filter_by(id=payment_id).first()
        if not payment:
            await callback.answer("پرداخت یافت نشد!")
            return
        
        if payment.status != PaymentStatus.PENDING:
            await callback.answer("این پرداخت قبلاً پردازش شده!")
            return
        
        user = session.query(User).filter_by(id=payment.user_id).first()
        
        payment.status = PaymentStatus.REJECTED
        payment.rejected_at = func.now()
        payment.admin_id = callback.from_user.id
        session.commit()
        
        try:
            await bot.send_message(
                user.telegram_id,
                f"❌ پرداخت شما رد شد.\n💰 مبلغ: {payment.amount:,.0f} تومان"
            )
        except:
            pass
        
        await safe_edit_text(
            callback.message,
            f"❌ پرداخت رد شد!\n"
            f"👤 @{user.username or 'ندارد'}\n"
            f"💰 {payment.amount:,.0f} تومان"
        )
        await callback.answer("❌ رد شد!")

@dp.callback_query(lambda c: c.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit_text(callback.message, "❌ لغو شد.", main_menu())
    await callback.answer()

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
