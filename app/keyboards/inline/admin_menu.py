from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """کیبورد داشبورد ادمین"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 کاربران", callback_data="admin:users")],
        [InlineKeyboardButton(text="🛒 سفارشات", callback_data="admin:orders")],
        [InlineKeyboardButton(text="💳 پرداخت‌ها", callback_data="admin:deposits")],
        [InlineKeyboardButton(text="💰 کیف پول", callback_data="admin:wallet")],
        [InlineKeyboardButton(text="📦 محصولات", callback_data="admin:products")],
        [InlineKeyboardButton(text="💵 قیمت‌ها", callback_data="admin:prices")],
        [InlineKeyboardButton(text="🎓 آموزش‌ها", callback_data="admin:tutorials")],
        [InlineKeyboardButton(text="🎧 پشتیبانی", callback_data="admin:support")],
        [InlineKeyboardButton(text="📢 پیام همگانی", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="admin:settings")]
    ])

def back_to_admin() -> InlineKeyboardMarkup:
    """بازگشت به داشبورد ادمین"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت به پنل مدیریت", callback_data="admin:dashboard")]
    ])
