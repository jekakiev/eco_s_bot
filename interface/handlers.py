from aiogram import Dispatcher, F, types
from .callbacks import (
    show_wallets, add_wallet_start, process_wallet_address, process_wallet_name,
    toggle_token, confirm_tokens, save_tokens, delete_wallet, rename_wallet_start,
    process_new_wallet_name, edit_tokens_start, show_tokens, add_token_start,
    process_contract_address, confirm_token_name, reject_token_name, thread_exists,
    thread_not_exists, process_thread_id, edit_token_start, edit_token_thread,
    process_edit_thread_id, delete_token, show_commands, go_home
)
from aiogram.filters import Command
from .states import WalletStates, TokenStates
from database import Database
from logger_config import logger

db = Database()

def register_handlers(dp: Dispatcher):
    dp.callback_query.register(show_wallets, F.data == "show_wallets")
    dp.callback_query.register(add_wallet_start, F.data == "add_wallet")
    dp.message.register(process_wallet_address, WalletStates.waiting_for_address)
    dp.message.register(process_wallet_name, WalletStates.waiting_for_name)
    dp.callback_query.register(toggle_token, F.data.startswith("toggle_token_"))
    dp.callback_query.register(confirm_tokens, F.data == "confirm_tokens")
    dp.callback_query.register(save_tokens, F.data == "save_tokens")
    dp.callback_query.register(delete_wallet, F.data.startswith("delete_wallet_"))
    dp.callback_query.register(rename_wallet_start, F.data.startswith("rename_wallet_"))
    dp.message.register(process_new_wallet_name, WalletStates.waiting_for_new_name)
    dp.callback_query.register(edit_tokens_start, F.data.startswith("edit_tokens_"))
    dp.callback_query.register(show_tokens, F.data == "show_tokens")
    dp.callback_query.register(add_token_start, F.data == "add_token")
    dp.message.register(process_contract_address, TokenStates.waiting_for_contract_address)
    dp.callback_query.register(confirm_token_name, F.data == "confirm_token_name")
    dp.callback_query.register(reject_token_name, F.data == "reject_token_name")
    dp.callback_query.register(thread_exists, F.data == "thread_exists")
    dp.callback_query.register(thread_not_exists, F.data == "thread_not_exists")
    dp.message.register(process_thread_id, TokenStates.waiting_for_thread_id)
    dp.callback_query.register(edit_token_start, F.data.startswith("edit_token_"))
    dp.callback_query.register(edit_token_thread, F.data.startswith("edit_token_"))
    dp.message.register(process_edit_thread_id, TokenStates.waiting_for_edit_thread_id)
    dp.callback_query.register(delete_token, F.data.startswith("delete_token_"))
    dp.callback_query.register(show_commands, F.data == "show_commands")
    dp.callback_query.register(go_home, F.data == "home")
    
    # Регистрация команд для кошельков
    wallet_commands = [f"Edit_{wallet['address'][-4:]}" for wallet in db.get_all_wallets()]
    if wallet_commands:
        dp.message.register(edit_wallet_command, Command(commands=wallet_commands))
    else:
        logger.warning("Нет кошельков для регистрации команд /Edit_XXXX")
    
    # Регистрация команд для токенов
    token_commands = [f"edit_{token['contract_address'][-4:]}" for token in db.get_all_tracked_tokens()]
    if token_commands:
        dp.message.register(edit_token_command, Command(commands=token_commands))
    else:
        logger.warning("Нет токенов для регистрации команд /edit_XXXX")

async def edit_wallet_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        short_address = message.text.split("_")[1]
        wallets = db.get_all_wallets()
        wallet = next((w for w in wallets if w["address"].endswith(short_address)), None)
        if not wallet:
            await message.answer("❌ Кошелек не найден.")
            return
        from .keyboards import get_wallet_control_keyboard
        text = f"Имя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
        await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet['id']))
    except Exception as e:
        logger.error(f"Ошибка обработки команды /Edit: {str(e)}")
        await message.answer("❌ Ошибка при обработке команды.")

async def edit_token_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        short_address = message.text.split("_")[1]
        tokens = db.get_all_tracked_tokens()
        token = next((t for t in tokens if t["contract_address"].endswith(short_address)), None)
        if not token:
            await message.answer("❌ Токен не найден.")
            return
        from .keyboards import get_token_control_keyboard
        text = f"Токен: {token['token_name']}\nАдрес: {token['contract_address']}\nТекущий тред: {token['thread_id']}"
        await message.answer(text, reply_markup=get_token_control_keyboard(token['id']))
    except Exception as e:
        logger.error(f"Ошибка обработки команды /edit: {str(e)}")
        await message.answer("❌ Ошибка при обработке команды.")