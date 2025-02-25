from aiogram import Dispatcher, F, types
from .callbacks.wallets import (
    show_wallets, add_wallet_start, process_wallet_address, process_wallet_name,
    toggle_token, confirm_tokens, save_tokens, delete_wallet, rename_wallet_start,
    process_new_wallet_name, edit_tokens_start
)
from .callbacks.tokens import (
    show_tokens, add_token_start, process_contract_address, confirm_token_name,
    reject_token_name, thread_exists, thread_not_exists, process_thread_id,
    edit_token_start, edit_token_thread, process_edit_thread_id, delete_token
)
from .callbacks.settings_callbacks import (
    show_commands, show_settings, edit_setting_start, process_setting_value,
    toggle_setting, go_home
)
from .callbacks.test_api_last_transaction import (
    show_test_api, select_wallet
)
from .callbacks.test_api_by_hash import (
    show_test_api_by_hash, request_transaction_hash
)
from aiogram.filters import Command
from .states import WalletStates, TokenStates, SettingStates
from database import Database
from utils.logger_config import logger

db = Database()

def register_handlers(dp: Dispatcher):
    logger.info("Регистрация обработчиков callback-запросов началась")
    
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
    dp.callback_query.register(edit_token_thread, F.data.startswith("edit_token_thread_"))
    dp.message.register(process_edit_thread_id, TokenStates.waiting_for_edit_thread_id)
    dp.callback_query.register(delete_token, F.data.startswith("delete_token_"))
    
    dp.callback_query.register(show_commands, F.data == "show_commands")
    dp.callback_query.register(show_settings, F.data == "show_settings")
    dp.callback_query.register(edit_setting_start, F.data.startswith("edit_setting_"))
    dp.callback_query.register(toggle_setting, F.data.startswith("toggle_"))
    dp.message.register(process_setting_value, SettingStates.waiting_for_setting_value)
    dp.callback_query.register(go_home, F.data == "home")
    
    dp.callback_query.register(show_test_api, F.data == "test_api_last_transaction")
    dp.callback_query.register(select_wallet, F.data.startswith("select_wallet_"))
    
    dp.callback_query.register(show_test_api_by_hash, F.data == "test_api_by_hash")
    dp.message.register(request_transaction_hash, WalletStates.waiting_for_transaction_hash)
    
    wallet_commands = [f"Edit_{wallet['address'][-4:]}" for wallet in db.wallets.get_all_wallets()]  # Оновлено на db.wallets.get_all_wallets()
    if wallet_commands:
        dp.message.register(edit_wallet_command, Command(commands=wallet_commands))
        logger.info(f"Зарегистрированы команды для кошельков: {wallet_commands}")
    else:
        if int(db.settings.get_setting("INTERFACE_INFO", "0")):
            logger.warning("Нет кошельков для регистрации команд /Edit_XXXX")
    
    token_commands = [f"edit_{token['contract_address'][-4:]}" for token in db.tracked_tokens.get_all_tracked_tokens()]  # Оновлено на db.tracked_tokens.get_all_tracked_tokens()
    if token_commands:
        dp.message.register(edit_token_command, Command(commands=token_commands))
        logger.info(f"Зарегистрированы команды для токенов: {token_commands}")
    else:
        if int(db.settings.get_setting("INTERFACE_INFO", "0")):
            logger.warning("Нет токенов для регистрации команд /edit_XXXX")

    logger.info("Регистрация обработчиков callback-запросов завершена")

async def edit_wallet_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        short_address = message.text.split("_")[1]
        wallets = db.wallets.get_all_wallets()  # Оновлено на db.wallets.get_all_wallets()
        wallet = next((w for w in wallets if w['address'].endswith(short_address)), None)
        if not wallet:
            await message.answer("❌ Кошелек не найден.")
            return
        from .keyboards import get_wallet_control_keyboard
        text = f"Имя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
        await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet['id']))
    except Exception as e:
        if int(db.settings.get_setting("API_ERRORS", "1")):
            logger.error(f"Ошибка обработки команды /Edit: {str(e)}")
        await message.answer("❌ Ошибка при обработке команды.")

async def edit_token_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        short_address = message.text.split("_")[1]
        tokens = db.tracked_tokens.get_all_tracked_tokens()  # Оновлено на db.tracked_tokens.get_all_tracked_tokens()
        token = next((t for t in tokens if t['contract_address'].endswith(short_address)), None)
        if not token:
            await message.answer("❌ Токен не найден.")
            return
        from .keyboards import get_token_control_keyboard
        text = f"Токен: {token['token_name']}\nАдрес: {token['contract_address']}\nТекущий тред: {token['thread_id']}"
        await message.answer(text, reply_markup=get_token_control_keyboard(token['id']))
    except Exception as e:
        if int(db.settings.get_setting("API_ERRORS", "1")):
            logger.error(f"Ошибка обработки команды /edit: {str(e)}")
        await message.answer("❌ Ошибка при обработке команды.")