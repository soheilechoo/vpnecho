from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy import func
import os

from database.database import db
from database.models import BankCard, ProductPrice, User, Order
from states.admin_states import AdminState
from keyboards.admin_keyboards import (
    get_admin_main_menu,
    get_prices_management_menu,
    get_product_selection_keyboard,
    get_card_management_menu,
    get_cards_list_keyboard,
    get_confirmation_keyboard,
    get_back_to_cards_keyboard,
    get_edit_card_keyboard
)

router = Router()

# ============================================================
# 1. منوی اصلی ادمین
# ============================================================

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    """ورود به پنل ادمین"""
    admin_id = int(os.getenv('ADMIN_IDS', '0'))
    
    if message.from_user.id != admin_id:
        await message.answer("⛔ شما دسترسی به این بخش ندارید.")
        return
    
    await message.answer(
        "👋 به پنل مدیریت خوش آمدید!\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_admin_main_menu()
    )

@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    """بازگشت به منوی اصلی ادمین"""
    await state.clear()
    await callback.message.edit_text(
        "👋 به پنل مدیریت خوش آمدید!\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_admin_main_menu()
    )
    await callback.answer()

# ============================================================
# 2. آمار
# ============================================================

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """نمایش آمار کلی"""
    with db.get_session() as session:
        total_users = session.query(User).count()
        total_orders = session.query(Order).count()
        pending_orders = session.query(Order).filter_by(status="pending").count()
        delivered_orders = session.query(Order).filter_by(status="delivered").count()
        total_revenue = session.query(Order).filter_by(status="delivered").with_entities(func.sum(Order.price)).scalar() or 0
        
        await callback.message.edit_text(
            f"📊 **آمار کلی**\n\n"
            f"👥 کاربران: {total_users}\n"
            f"🛒 سفارش‌ها: {total_orders}\n"
            f"⏳ در انتظار: {pending_orders}\n"
            f"✅ تحویل‌شده: {delivered_orders}\n"
            f"💰 درآمد کل: {total_revenue:,.0f} تومان",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
            ])
        )
    await callback.answer()

# ============================================================
# 3. کاربران
# ============================================================

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """مدیریت کاربران"""
    with db.get_session() as session:
        total_users = session.query(User).count()
        active_users = session.query(User).filter_by(is_active=True).count() if hasattr(User, 'is_active') else total_users
        blocked_users = total_users - active_users
        
        await callback.message.edit_text(
            f"👥 **مدیریت کاربران**\n\n"
            f"📊 تعداد کل کاربران: {total_users}\n"
            f"✅ کاربران فعال: {active_users}\n"
            f"🚫 کاربران مسدود: {blocked_users}\n\n"
            "برای جستجوی کاربر از دکمه زیر استفاده کنید:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔎 جستجوی کاربر", callback_data="admin_search")],
                [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
            ])
        )
    await callback.answer()

# ============================================================
# 4. مدیریت قیمت‌ها
# ============================================================

@dp.callback_query(F.data == "admin_prices")
async def manage_prices(callback: CallbackQuery):
    """نمایش مدیریت قیمت‌ها"""
    with db.get_session() as session:
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
        
        price_text = "📋 **مدیریت قیمت‌ها**\n\n"
        product_names = {
            "vip_single": "🟣 VIP تک کاربره",
            "vip_dual": "🟣 VIP دو کاربره",
            "normal_single": "🔵 معمولی تک کاربره",
            "normal_dual": "🔵 معمولی دو کاربره"
        }
        for p in prices:
            name = product_names.get(p.product_type, p.product_type)
            price_text += f"{name}: **{p.price:,.0f}** تومان\n"
        
        await callback.message.edit_text(
            price_text,
            reply_markup=get_prices_management_menu(),
            parse_mode="Markdown"
        )
    await callback.answer()

@dp.callback_query(F.data == "edit_price")
async def select_product_for_price_edit(callback: CallbackQuery, state: FSMContext):
    """انتخاب محصول برای ویرایش قیمت"""
    with db.get_session() as session:
        products = session.query(ProductPrice).all()
        await callback.message.edit_text(
            "📝 لطفاً سرویس مورد نظر برای تغییر قیمت را انتخاب کنید:",
            reply_markup=get_product_selection_keyboard(products)
        )
        await state.set_state(AdminState.waiting_for_product_selection)
    await callback.answer()

@dp.callback_query(F.data.startswith("price_product_"), AdminState.waiting_for_product_selection)
async def get_new_price(callback: CallbackQuery, state: FSMContext):
    """دریافت قیمت جدید"""
    product_type = callback.data.replace("price_product_", "")
    await state.update_data(product_type=product_type)
    
    with db.get_session() as session:
        product = session.query(ProductPrice).filter_by(product_type=product_type).first()
        product_names = {
            "vip_single": "VIP تک کاربره",
            "vip_dual": "VIP دو کاربره",
            "normal_single": "معمولی تک کاربره",
            "normal_dual": "معمولی دو کاربره"
        }
        name = product_names.get(product_type, product_type)
        
        await callback.message.edit_text(
            f"💰 قیمت جدید برای **{name}** را وارد کنید:\n\n"
            f"قیمت فعلی: **{product.price:,.0f}** تومان\n\n"
            "لطفاً فقط عدد وارد کنید:",
            parse_mode="Markdown"
        )
        await state.set_state(AdminState.waiting_for_new_price)
    await callback.answer()

@dp.message(AdminState.waiting_for_new_price)
async def save_new_price(message: Message, state: FSMContext):
    """ذخیره قیمت جدید"""
    try:
        new_price = float(message.text.strip())
        if new_price < 0:
            await message.answer("❌ قیمت نمی‌تواند منفی باشد. دوباره وارد کنید:")
            return
        
        data = await state.get_data()
        product_type = data.get('product_type')
        
        with db.get_session() as session:
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
                await manage_prices(message)
            else:
                await message.answer("❌ محصول یافت نشد.")
                
    except ValueError:
        await message.answer("❌ لطفاً فقط عدد وارد کنید:")

# ============================================================
# 5. مدیریت کارت‌های بانکی
# ============================================================

@dp.callback_query(F.data == "admin_cards")
async def manage_cards(callback: CallbackQuery):
    """منوی مدیریت کارت‌های بانکی"""
    await callback.message.edit_text(
        "💳 **مدیریت شماره کارت‌ها**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_card_management_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============================================================
# 5.1. افزودن شماره کارت
# ============================================================

@dp.callback_query(F.data == "add_card")
async def add_card_start(callback: CallbackQuery, state: FSMContext):
    """شروع فرآیند افزودن کارت"""
    await state.set_state(AdminState.waiting_for_card_number)
    await callback.message.edit_text(
        "💳 **افزودن شماره کارت جدید**\n\n"
        "لطفاً شماره کارت (۱۶ رقم) را وارد کنید:\n"
        "مثال: `6037997512345678`\n\n"
        "یا برای بازگشت روی دکمه زیر کلیک کنید:",
        parse_mode="Markdown",
        reply_markup=get_back_to_cards_keyboard()
    )
    await callback.answer()

@dp.message(AdminState.waiting_for_card_number)
async def process_card_number(message: Message, state: FSMContext):
    """پردازش شماره کارت"""
    card_number = message.text.strip().replace(" ", "").replace("-", "")
    
    if not card_number.isdigit():
        await message.answer(
            "❌ **شماره کارت نامعتبر است!**\n\n"
            "شماره کارت باید فقط شامل **عدد** باشد.\n"
            "لطفاً دوباره وارد کنید:",
            parse_mode="Markdown"
        )
        return
    
    if len(card_number) != 16:
        await message.answer(
            f"❌ **شماره کارت نامعتبر است!**\n\n"
            f"شماره کارت باید **۱۶ رقم** باشد.\n"
            f"شما {len(card_number)} رقم وارد کردید.\n\n"
            "لطفاً دوباره وارد کنید:",
            parse_mode="Markdown"
        )
        return
    
    with db.get_session() as session:
        existing = session.query(BankCard).filter_by(card_number=card_number).first()
        if existing:
            await message.answer(
                "❌ **این شماره کارت قبلاً ثبت شده است!**\n\n"
                "لطفاً شماره کارت دیگری وارد کنید:",
                parse_mode="Markdown"
            )
            return
    
    await state.update_data(card_number=card_number)
    await state.set_state(AdminState.waiting_for_card_holder)
    
    formatted = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
    
    await message.answer(
        f"✅ شماره کارت: `{formatted}`\n\n"
        "👤 **نام صاحب کارت** را وارد کنید:\n"
        "مثال: `علی رضایی`",
        parse_mode="Markdown"
    )

@dp.message(AdminState.waiting_for_card_holder)
async def process_card_holder(message: Message, state: FSMContext):
    """پردازش نام صاحب کارت"""
    card_holder = message.text.strip()
    
    if len(card_holder) < 3:
        await message.answer(
            "❌ **نام صاحب کارت نامعتبر است!**\n\n"
            "نام باید حداقل **۳ کاراکتر** باشد.\n"
            "لطفاً دوباره وارد کنید:",
            parse_mode="Markdown"
        )
        return
    
    data = await state.get_data()
    card_number = data.get('card_number')
    formatted = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
    
    await state.update_data(card_holder=card_holder)
    await state.set_state(AdminState.confirm_card)
    
    await message.answer(
        f"📋 **تأیید اطلاعات کارت جدید**\n\n"
        f"💳 شماره کارت: `{formatted}`\n"
        f"👤 صاحب کارت: **{card_holder}**\n\n"
        "آیا اطلاعات صحیح است؟",
        reply_markup=get_confirmation_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "confirm_card", AdminState.confirm_card)
async def save_card(callback: CallbackQuery, state: FSMContext):
    """ذخیره کارت جدید"""
    data = await state.get_data()
    card_number = data.get('card_number')
    card_holder = data.get('card_holder')
    formatted = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
    
    with db.get_session() as session:
        new_card = BankCard(
            card_number=card_number,
            card_holder_name=card_holder,
            is_active=True
        )
        session.add(new_card)
        session.commit()
        
        await callback.message.edit_text(
            f"✅ **شماره کارت با موفقیت اضافه شد!**\n\n"
            f"💳 شماره کارت: `{formatted}`\n"
            f"👤 صاحب کارت: **{card_holder}**",
            parse_mode="Markdown",
            reply_markup=get_card_management_menu()
        )
        await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel_card")
async def cancel_card(callback: CallbackQuery, state: FSMContext):
    """لغو افزودن کارت"""
    await state.clear()
    await callback.message.edit_text(
        "❌ عملیات افزودن کارت لغو شد.",
        reply_markup=get_card_management_menu()
    )
    await callback.answer()

# ============================================================
# 5.2. لیست شماره کارت‌ها
# ============================================================

@dp.callback_query(F.data == "list_cards")
async def list_cards(callback: CallbackQuery):
    """نمایش لیست کارت‌ها"""
    with db.get_session() as session:
        cards = session.query(BankCard).filter_by(is_active=True).all()
        
        if not cards:
            await callback.message.edit_text(
                "📭 **هیچ شماره کارتی ثبت نشده است.**",
                parse_mode="Markdown",
                reply_markup=get_card_management_menu()
            )
            await callback.answer()
            return
        
        text = "📋 **لیست شماره کارت‌ها:**\n\n"
        for idx, card in enumerate(cards, 1):
            formatted = " ".join([card.card_number[i:i+4] for i in range(0, 16, 4)])
            text += f"{idx}. 💳 `{formatted}`\n"
            text += f"   👤 {card.card_holder_name}\n"
            text += f"   🆔 شناسه: {card.id}\n\n"
        
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_cards_list_keyboard(cards)
        )
    await callback.answer()

# ============================================================
# 5.3. ویرایش شماره کارت
# ============================================================

@dp.callback_query(F.data.startswith("edit_card_"))
async def edit_card_start(callback: CallbackQuery, state: FSMContext):
    """شروع ویرایش کارت"""
    card_id = int(callback.data.replace("edit_card_", ""))
    
    with db.get_session() as session:
        card = session.query(BankCard).filter_by(id=card_id).first()
        if not card:
            await callback.answer("کارت یافت نشد!")
            return
        
        formatted = " ".join([card.card_number[i:i+4] for i in range(0, 16, 4)])
        
        await state.update_data(card_id=card_id)
        await callback.message.edit_text(
            f"✏️ **ویرایش کارت**\n\n"
            f"💳 شماره کارت: `{formatted}`\n"
            f"👤 صاحب کارت: {card.card_holder_name}\n\n"
            "لطفاً **شماره کارت جدید** (۱۶ رقم) را وارد کنید.\n"
            "یا برای تغییر فقط نام، روی دکمه زیر کلیک کنید:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✏️ فقط تغییر نام", callback_data="edit_card_holder_only")],
                [InlineKeyboardButton(text="↩️ بازگشت", callback_data="admin_cards")]
            ])
        )
        await state.set_state(AdminState.waiting_for_card_number_edit)
    await callback.answer()

@dp.message(AdminState.waiting_for_card_number_edit)
async def process_card_number_edit(message: Message, state: FSMContext):
    """پردازش شماره کارت جدید برای ویرایش"""
    card_number = message.text.strip().replace(" ", "").replace("-", "")
    
    if not card_number.isdigit() or len(card_number) != 16:
        await message.answer(
            "❌ **شماره کارت نامعتبر است!**\n\n"
            "لطفاً یک شماره کارت ۱۶ رقمی وارد کنید:"
        )
        return
    
    data = await state.get_data()
    card_id = data.get('card_id')
    
    with db.get_session() as session:
        card = session.query(BankCard).filter_by(id=card_id).first()
        if card:
            card.card_number = card_number
            session.commit()
            formatted = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
            
            await message.answer(
                f"✅ **شماره کارت با موفقیت ویرایش شد!**\n\n"
                f"💳 شماره کارت جدید: `{formatted}`",
                parse_mode="Markdown",
                reply_markup=get_card_management_menu()
            )
            await state.clear()

@dp.callback_query(F.data == "edit_card_holder_only", AdminState.waiting_for_card_number_edit)
async def edit_holder_only(callback: CallbackQuery, state: FSMContext):
    """فقط ویرایش نام صاحب کارت"""
    await callback.message.edit_text(
        "👤 **نام جدید صاحب کارت** را وارد کنید:"
    )
    await state.set_state(AdminState.waiting_for_card_holder_edit)
    await callback.answer()

@dp.message(AdminState.waiting_for_card_holder_edit)
async def process_card_holder_edit(message: Message, state: FSMContext):
    """پردازش نام جدید صاحب کارت"""
    card_holder = message.text.strip()
    
    if len(card_holder) < 3:
        await message.answer("❌ نام باید حداقل ۳ کاراکتر باشد. دوباره وارد کنید:")
        return
    
    data = await state.get_data()
    card_id = data.get('card_id')
    
    with db.get_session() as session:
        card = session.query(BankCard).filter_by(id=card_id).first()
        if card:
            card.card_holder_name = card_holder
            session.commit()
            
            await message.answer(
                f"✅ **نام صاحب کارت با موفقیت ویرایش شد!**\n\n"
                f"👤 نام جدید: {card_holder}",
                reply_markup=get_card_management_menu()
            )
            await state.clear()

# ============================================================
# 5.4. حذف شماره کارت
# ============================================================

@dp.callback_query(F.data.startswith("delete_card_"))
async def delete_card(callback: CallbackQuery, state: FSMContext):
    """حذف شماره کارت"""
    card_id = int(callback.data.replace("delete_card_", ""))
    
    with db.get_session() as session:
        card = session.query(BankCard).filter_by(id=card_id).first()
        if not card:
            await callback.answer("کارت یافت نشد!")
            return
        
        formatted = " ".join([card.card_number[i:i+4] for i in range(0, 16, 4)])
        
        await state.update_data(card_id=card_id)
        await callback.message.edit_text(
            f"⚠️ **آیا مطمئن هستید؟**\n\n"
            f"شماره کارت: `{formatted}`\n"
            f"صاحب کارت: {card.card_holder_name}\n\n"
            "آیا می‌خواهید این شماره کارت را حذف کنید؟",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ بله، حذف شود", callback_data="confirm_delete_card"),
                    InlineKeyboardButton(text="❌ لغو", callback_data="cancel_delete_card")
                ]
            ]),
            parse_mode="Markdown"
        )
    await callback.answer()

@dp.callback_query(F.data == "confirm_delete_card")
async def confirm_delete_card(callback: CallbackQuery, state: FSMContext):
    """تأیید حذف کارت"""
    data = await state.get_data()
    card_id = data.get('card_id')
    
    if not card_id:
        await callback.answer("خطا! لطفاً دوباره تلاش کنید.")
        return
    
    with db.get_session() as session:
        card = session.query(BankCard).filter_by(id=card_id).first()
        if card:
            card.is_active = False
            session.commit()
            formatted = " ".join([card.card_number[i:i+4] for i in range(0, 16, 4)])
            await callback.message.edit_text(
                f"✅ **شماره کارت با موفقیت حذف شد!**\n\n"
                f"💳 `{formatted}`",
                parse_mode="Markdown",
                reply_markup=get_card_management_menu()
            )
        else:
            await callback.message.edit_text(
                "❌ کارت یافت نشد!",
                reply_markup=get_card_management_menu()
            )
        await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel_delete_card")
async def cancel_delete_card(callback: CallbackQuery, state: FSMContext):
    """لغو حذف کارت"""
    await state.clear()
    await callback.message.edit_text(
        "❌ عملیات حذف لغو شد.",
        reply_markup=get_card_management_menu()
    )
    await callback.answer()

# ============================================================
# 6. سایر دکمه‌ها
# ============================================================

@dp.callback_query(F.data == "admin_search")
async def admin_search(callback: CallbackQuery, state: FSMContext):
    """جستجوی کاربر"""
    await callback.message.edit_text(
        "🔎 **جستجوی کاربر**\n\n"
        "لطفاً **شناسه تلگرام** یا **یوزرنیم** کاربر را وارد کنید:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت", callback_data="back_to_admin")]
        ])
    )
    await state.set_state(AdminState.waiting_for_user_search)
    await callback.answer()

@dp.message(AdminState.waiting_for_user_search)
async def search_user(message: Message, state: FSMContext):
    """جستجوی کاربر"""
    query = message.text.strip()
    
    with db.get_session() as session:
        if query.isdigit():
            user = session.query(User).filter_by(telegram_id=int(query)).first()
        else:
            user = session.query(User).filter_by(username=query.replace("@", "")).first()
        
        if user:
            await message.answer(
                f"👤 **اطلاعات کاربر**\n\n"
                f"🆔 شناسه: {user.telegram_id}\n"
                f"👤 نام: {user.first_name or 'نامشخص'}\n"
                f"📱 یوزرنیم: @{user.username or 'ندارد'}\n"
                f"💰 موجودی: {user.wallet.balance if user.wallet else 0:,.0f} تومان\n"
                f"📅 تاریخ عضویت: {user.created_at.strftime('%Y-%m-%d %H:%M')}",
                parse_mode="Markdown",
                reply_markup=get_admin_main_menu()
            )
        else:
            await message.answer("❌ کاربری با این مشخصات یافت نشد.")
        await state.clear()

@dp.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    """تنظیمات"""
    card_number = os.getenv('CARD_NUMBER', '6037-9912-3456-7890')
    card_owner = os.getenv('CARD_OWNER', 'ECHO VPN')
    
    await callback.message.edit_text(
        f"⚙️ **تنظیمات**\n\n"
        f"💳 شماره کارت: `{card_number}`\n"
        f"👤 صاحب کارت: {card_owner}\n\n"
        "برای تغییر شماره کارت از بخش **مدیریت شماره کارت** استفاده کنید.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

# ============================================================
# 7. دکمه‌های placeholder (در حال توسعه)
# ============================================================

@dp.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    """سفارش‌ها - placeholder"""
    await callback.message.edit_text(
        "🛒 **سفارش‌ها**\n\n"
        "این بخش در حال توسعه است...\n"
        "به زودی اضافه می‌شود.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_wallets")
async def admin_wallets(callback: CallbackQuery):
    """کیف پول‌ها - placeholder"""
    await callback.message.edit_text(
        "💰 **کیف پول‌ها**\n\n"
        "این بخش در حال توسعه است...\n"
        "به زودی اضافه می‌شود.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_payments")
async def admin_payments(callback: CallbackQuery):
    """پرداخت‌ها - placeholder"""
    await callback.message.edit_text(
        "💳 **پرداخت‌ها**\n\n"
        "این بخش در حال توسعه است...\n"
        "به زودی اضافه می‌شود.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_tutorials")
async def admin_tutorials(callback: CallbackQuery):
    """آموزش‌ها - placeholder"""
    await callback.message.edit_text(
        "🎓 **آموزش‌ها**\n\n"
        "این بخش در حال توسعه است...\n"
        "به زودی اضافه می‌شود.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery):
    """ارسال پیام همگانی - placeholder"""
    await callback.message.edit_text(
        "📢 **ارسال پیام همگانی**\n\n"
        "این بخش در حال توسعه است...\n"
        "به زودی اضافه می‌شود.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
        ])
    )
    await callback.answer()

# ============================================================
# ثبت روت
# ============================================================

def register_admin_handlers(dp):
    dp.include_router(router)
