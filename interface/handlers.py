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
from utils.logger_config import logger, should_log

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
    
    # Оновлено для работы с последними 4 символами адреса
    wallets = db.wallets.get_all_wallets()
    wallet_commands = [f"Editw_{wallet[1][-4:]}" for wallet in wallets]  # wallet[1] — address (последние 4 символа)
    if wallet_commands:
        dp.message.register(edit_wallet_command, Command(commands=wallet_commands))
        logger.info(f"Зарегистрированы команды для кошельков: {wallet_commands}")
    else:
        if should_log("interface"):
            logger.warning("Нет кошельков для регистрации команд /Editw_XXXX")
    
    # Оновлено для работы с кортежами
    tokens = db.tracked_tokens.get_all_tracked_tokens()
    token_commands = [f"edit_{token[1][-4:]}" for token in tokens]  # token[1] — contract_address (последние 4 символа)
    if token_commands:
        dp.message.register(edit_token_command, Command(commands=token_commands))
        logger.info(f"Зарегистрированы команды для токенов: {token_commands}")
    else:
        if should_log("interface"):
            logger.warning("Нет токенов для регистрации команд /edit_XXXX")

    logger.info("Регистрация обработчиков callback-запросов завершена")

async def edit_wallet_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        if not message.text.startswith("/Editw_"):
            await message.answer("❌ Неверный формат команды. Используйте /Editw_XXXX (последние 4 символа адреса кошелька).")
            return
        short_address = message.text.replace("/Editw_", "")
        if len(short_address) != 4:
            await message.answer("❌ Последние 4 символа адреса должны быть указаны (например, /Editw_68B8).")
            return
        if should_log("debug"):
            logger.debug(f"Попытка найти кошелек с последними 4 символами адреса: {short_address}, полный текст команды: {message.text}")
        db.reconnect()
        wallets = db.wallets.get_all_wallets()  # Отримуємо кортежі
        if should_log("debug"):
            logger.debug(f"Список кошельков из базы: {wallets}")
        wallet = next((w for w in wallets if w[1].endswith(short_address)), None)  # w[1] — address
        if not wallet:
            if should_log("debug"):
                logger.debug(f"Кошелек с последними 4 символами {short_address} не найден в базе: {wallets}")
            await message.answer("❌ Кошелек не найден.")
            return
        if should_log("debug"):
            logger.debug(f"Кошелек найден: ID={wallet[0]}, Адрес={wallet[1]}, Имя={wallet[2]}, Токены={wallet[3]}")
        from .keyboards import get_wallet_control_keyboard
        text = f"Имя кошелька: {wallet[2]}\nАдрес кошелька: {wallet[1]}"  # wallet[2] — name, wallet[1] — address
        try:
            sent_message = await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet[0]))  # wallet[0] — id
        except Exception as e:
            if int(db.settings.get_setting("API_ERRORS", "1")):
                logger.error(f"Ошибка при отправке сообщения для кошелька с адресом {wallet[1][-4:]}: {str(e)}", exc_info=True)
            await message.answer("❌ Ошибка при отправке данных кошелька.")
            return
        # Удаляем сообщение пользователя с командой
        await message.delete()
    except Exception as e:
        if int(db.settings.get_setting("API_ERRORS", "1")):
            logger.error(f"Ошибка обработки команды /Editw: {str(e)}", exc_info=True)  # Логируем полный стек вызовов
        if should_log("debug"):
            logger.debug(f"Состояние подключения к базе после ошибки: {db.connection.is_connected() if db.connection else 'Нет подключения'}")
            logger.debug(f"Список кошельков после ошибки: {db.wallets.get_all_wallets()}")
        await message.answer("❌ Ошибка при обработке команды.")

async def edit_token_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        short_address = message.text.split("_")[1]
        db.reconnect()
        tokens = db.tracked_tokens.get_all_tracked_tokens()  # Отримуємо кортежі
        if should_log("debug"):
            logger.debug(f"Список токенов из базы: {tokens}")
        token = next((t for t in tokens if t[1].endswith(short_address)), None)  # t[1] — contract_address
        if not token:
            if should_log("debug"):
                logger.debug(f"Токен с последними 4 символами {short_address} не найден в базе: {tokens}")
            await message.answer("❌ Токен не найден.")
            return
        from .keyboards import get_token_control_keyboard
        text = f"Токен: {token[2]}\nАдрес: {token[1]}\nТекущий тред: {token[3]}"  # token[2] — token_name, token[1] — contract_address, token[3] — thread_id
        sent_message = await message.answer(text, reply_markup=get_token_control_keyboard(token[0]))  # token[0] — id
        # Удаляем сообщение пользователя с командой
        await message.delete()
    except Exception as e:
        if int(db.settings.get_setting("API_ERRORS", "1")):
            logger.error(f"Ошибка обработки команды /edit: {str(e)}", exc_info=True)  # Логируем полный стек вызовов
        await message.answer("❌ Ошибка при обработке команды.")