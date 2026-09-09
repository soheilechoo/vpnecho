from aiogram.fsm.state import State, StatesGroup

class WalletState(StatesGroup):
    entering_amount = State()  # مرحله وارد کردن مبلغ
    sending_receipt = State()  # مرحله ارسال رسید
