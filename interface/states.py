from aiogram.fsm.state import StatesGroup, State

class WalletStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_name = State()
    waiting_for_tokens = State()
    waiting_for_new_name = State()

class TokenStates(StatesGroup):
    waiting_for_contract_address = State()
    waiting_for_name_confirmation = State()
    waiting_for_thread_confirmation = State()
    waiting_for_thread_id = State()
    waiting_for_edit_thread_id = State()