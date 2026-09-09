from aiogram.fsm.state import State, StatesGroup

class AdminState(StatesGroup):
    # مدیریت قیمت‌ها
    waiting_for_product_selection = State()
    waiting_for_new_price = State()
    
    # مدیریت کارت‌های بانکی
    waiting_for_card_number = State()
    waiting_for_card_holder = State()
    confirm_card = State()
    
    # مدیریت کاربران
    waiting_for_user_search = State()
    waiting_for_block_reason = State()
    
    # ویرایش کارت
    waiting_for_card_number_edit = State()
    waiting_for_card_holder_edit = State()
