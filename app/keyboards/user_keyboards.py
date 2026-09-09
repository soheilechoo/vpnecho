from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard():
    """منوی اصلی"""
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

def get_wallet_keyboard():
    """کیبورد مدیریت کیف پول"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 موجودی من", callback_data="balance")],
        [InlineKeyboardButton(text="➕ افزایش موجودی", callback_data="deposit")],
        [InlineKeyboardButton(text="📜 تاریخچه تراکنش‌ها", callback_data="transactions")],
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="main_menu")]
    ])

def get_back_keyboard():
    """کیبورد بازگشت"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ بازگشت", callback_data="main_menu")]
    ])
