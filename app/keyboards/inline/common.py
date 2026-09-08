from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.menu_service import MenuService
from app.database.session import get_db_session

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """منوی اصلی"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟣 خرید VPN VIP", callback_data="menu:PRODUCT_CATEGORY:VIP")],
        [InlineKeyboardButton(text="🔵 خرید VPN معمولی", callback_data="menu:PRODUCT_CATEGORY:NORMAL")],
        [InlineKeyboardButton(text="🎓 آموزش", callback_data="menu:TUTORIALS:")],
        [InlineKeyboardButton(text="💰 موجودی و افزایش موجودی", callback_data="menu:WALLET:")],
        [InlineKeyboardButton(text="🎧 پشتیبانی", callback_data="menu:SUPPORT:")]
    ])

def back_button(callback_data: str = "menu:BACK:") -> InlineKeyboardMarkup:
    """دکمه بازگشت"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data=callback_data)]
    ])

def back_to_main_button() -> InlineKeyboardMarkup:
    """دکمه بازگشت به منوی اصلی"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="menu:MAIN_MENU:")]
    ])

def back_with_main_button() -> InlineKeyboardMarkup:
    """دکمه‌های بازگشت و منوی اصلی"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu:BACK:")],
        [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="menu:MAIN_MENU:")]
    ])
