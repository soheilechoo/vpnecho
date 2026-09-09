from aiogram.fsm.state import State, StatesGroup

class WalletState(StatesGroup):
    entering_amount = State()
    sending_receipt = State()
