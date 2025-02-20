from aiogram.fsm.state import StatesGroup, State

class WalletStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_name = State()
    waiting_for_tokens = State()
    waiting_for_new_name = State()
