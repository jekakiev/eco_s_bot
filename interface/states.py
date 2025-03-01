# /interface/states.py
from aiogram.fsm.state import State, StatesGroup

class WalletStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_name = State()
    waiting_for_tokens = State()
    waiting_for_new_name = State()
    waiting_for_transaction_hash = State()

class TokenStates(StatesGroup):
    waiting_for_contract_address = State()
    waiting_for_name_confirmation = State()
    waiting_for_add_to_all_confirmation = State()  # Новое состояние
    waiting_for_thread_confirmation = State()
    waiting_for_thread_id = State()
    waiting_for_edit_thread_id = State()

class SettingStates(StatesGroup):
    waiting_for_setting_value = State()