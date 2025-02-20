from aiogram import Dispatcher
from .callbacks import (
    show_wallets, add_wallet_start, process_wallet_address, process_wallet_name,
    toggle_token, confirm_tokens, delete_wallet, rename_wallet_start, process_new_wallet_name,
    edit_wallet, go_home
)
from aiogram.filters import Command
from .states import WalletStates

# === РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ===
def register_handlers(dp: Dispatcher):
    dp.callback_query.register(show_wallets, F.data == "show_wallets")
    dp.callback_query.register(add_wallet_start, F.data == "add_wallet")
    dp.message.register(process_wallet_address, WalletStates.waiting_for_address)
    dp.message.register(process_wallet_name, WalletStates.waiting_for_name)
    dp.callback_query.register(toggle_token, F.data.startswith("toggle_token_"))
    dp.callback_query.register(confirm_tokens, F.data == "confirm_tokens")
    dp.callback_query.register(delete_wallet, F.data.startswith("delete_wallet_"))
    dp.callback_query.register(rename_wallet_start, F.data.startswith("rename_wallet_"))
    dp.message.register(process_new_wallet_name, WalletStates.waiting_for_new_name)
    dp.callback_query.register(edit_wallet, F.data.startswith("EDITw_"))
    dp.callback_query.register(go_home, F.data == "home")
