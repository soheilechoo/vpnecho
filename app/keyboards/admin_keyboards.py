from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_menu():
    """منوی اصلی ادمین"""
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

def get_prices_management_menu():
    """منوی مدیریت قیمت‌ها"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ ویرایش قیمت", callback_data="edit_price")],
        [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
    ])

def get_product_selection_keyboard(products):
    """کیبورد انتخاب محصول برای ویرایش قیمت"""
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

def get_card_management_menu():
    """منوی مدیریت کارت‌های بانکی"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ افزودن شماره کارت", callback_data="add_card")],
        [InlineKeyboardButton(text="📋 لیست شماره کارت‌ها", callback_data="list_cards")],
        [InlineKeyboardButton(text="↩️ بازگشت به پنل", callback_data="back_to_admin")]
    ])

def get_cards_list_keyboard(cards):
    """کیبورد لیست کارت‌ها با گزینه‌های ویرایش و حذف"""
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

def get_confirmation_keyboard():
    """کیبورد تأیید"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تایید و ذخیره", callback_data="confirm_card"),
            InlineKeyboardButton(text="❌ لغو", callback_data="cancel_card")
        ]
    ])

def get_back_to_cards_keyboard():
    """کیبورد بازگشت به مدیریت کارت‌ها"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="admin_cards")]
    ])

def get_edit_card_keyboard():
    """کیبورد ویرایش کارت"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ فقط تغییر نام", callback_data="edit_card_holder_only")],
        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="admin_cards")]
    ])
