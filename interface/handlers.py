# /interface/handlers.py
from aiogram import Dispatcher, F, types
from aiogram.filters import Command
from .callbacks.wallets import (
    show_wallets, add_wallet_start, process_wallet_address, process_wallet_name,
    toggle_token, confirm_tokens, save_tokens, delete_wallet, rename_wallet_start,
    process_new_wallet_name, edit_tokens_start
)
from .callbacks.tokens import (
    show_tokens, add_token_start, process_contract_address, confirm_token_name,
    reject_token_name, thread_exists, thread_not_exists, process_thread_id,
    edit_token_start, edit_token_thread, process_edit_thread_id, delete_token,
    add_to_all_yes, add_to_all_no
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
from .states import WalletStates, TokenStates, SettingStates
from db import Database
from utils.logger_config import logger, should_log
import re

db = Database()

def register_handlers(dp: Dispatcher):
    if should_log("interface"):
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
    dp.callback_query.register(add_to_all_yes, F.data == "add_to_all_yes")
    dp.callback_query.register(add_to_all_no, F.data == "add_to_all_no")
    
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
    
    wallets = db.wallets.get_all_wallets()
    wallet_commands = [f"Editw_{wallet[1][-4:]}" for wallet in wallets]
    if wallet_commands:
        dp.message.register(edit_wallet_command, Command(commands=wallet_commands))
        if should_log("interface"):
            logger.info(f"Зарегистрированы команды для кошельков: {wallet_commands}")
    else:
        if should_log("interface"):
            logger.warning("Нет кошельков для регистрации команд /Editw_XXXX")
    
    dp.message.register(edit_token_command, F.text.regexp(r"^/edit_\w{4}$"))
    dp.message.register(get_thread_id_command, Command(commands=["get_thread_id"]))

    # Добавляем явную отладку регистрации
    logger.info("Зарегистрирован обработчик edit_token_thread для callback_data 'edit_token_thread_'")

    if should_log("interface"):
        logger.info("Регистрация обработчиков callback-запросов завершена")

async def edit_wallet_command(message: types.Message):
    if should_log("interface"):
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
        wallets = db.wallets.get_all_wallets()
        if should_log("debug"):
            logger.debug(f"Список кошельков из базы: {wallets}")
        wallet = next((w for w in wallets if w[1].endswith(short_address)), None)
        if not wallet:
            if should_log("debug"):
                logger.debug(f"Кошелек с последними 4 символами {short_address} не найден в базе: {wallets}")
            await message.answer("❌ Кошелек не найден.")
            return
        
        try:
            name_cleaned = wallet[2].strip()
            address_cleaned = wallet[1].strip()
            if not name_cleaned or not address_cleaned:
                if should_log("debug"):
                    logger.debug(f"Очищенные данные пустые: name={name_cleaned}, address={address_cleaned}")
                await message.answer("❌ Кошелек содержит некорректные данные.")
                return
            name_cleaned.encode('utf-8')
            address_cleaned.encode('utf-8')
        except UnicodeEncodeError as e:
            if should_log("debug"):
                logger.debug(f"Ошибка кодировки для данных кошелька: name={wallet[2]}, address={wallet[1]}, ошибка={str(e)}")
            await message.answer("❌ Ошибка кодировки данных кошелька.")
            return
        
        if should_log("debug"):
            logger.debug(f"Кошелек найден: ID={wallet[0]}, Адрес={wallet[1]}, Имя={wallet[2]}, Токены={wallet[3]}")
        
        from .keyboards import get_wallet_control_keyboard
        try:
            text = f"Кошелек: {name_cleaned} ({address_cleaned[-4:]})"
            if should_log("debug"):
                logger.debug(f"Сформирован текст: {text}")
            
            keyboard = get_wallet_control_keyboard(wallet[0])
            if should_log("debug"):
                logger.debug(f"Сформирована клавиатура: {keyboard.inline_keyboard}")
            
            sent_message = await message.answer(text, reply_markup=keyboard)
            await message.delete()
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения для кошелька с адресом {address_cleaned[-4:]}: {str(e)}", exc_info=True)
            await message.answer("❌ Ошибка при отправке данных кошелька.")
            return
    
    except Exception as e:
        logger.error(f"Ошибка обработки команды /Editw: {str(e)}", exc_info=True)
        if should_log("debug"):
            logger.debug(f"Состояние подключения к базе после ошибки: {db.connection.is_connected() if db.connection else 'Нет подключения'}")
            logger.debug(f"Список кошельков после ошибки: {db.wallets.get_all_wallets()}")
        await message.answer("❌ Ошибка при обработке команды.")

async def edit_token_command(message: types.Message):
    if should_log("interface"):
        logger.info(f"Получена команда: {message.text}")
    try:
        if not message.text.startswith("/edit_"):
            await message.answer("❌ Неверный формат команды. Используйте /edit_XXXX (последние 4 символа адреса токена).")
            return
        short_address = message.text.replace("/edit_", "")
        if len(short_address) != 4:
            await message.answer("❌ Последние 4 символа адреса должны быть указаны (например, /edit_70ef).")
            return
        if should_log("debug"):
            logger.debug(f"Попытка найти токен с последними 4 символами адреса: {short_address}")
        db.reconnect()
        tokens = db.tracked_tokens.get_all_tracked_tokens()
        if should_log("debug"):
            logger.debug(f"Список токенов из базы: {tokens}")
        token = next((t for t in tokens if t[1].endswith(short_address)), None)
        if not token:
            if should_log("debug"):
                logger.debug(f"Токен с последними 4 символами {short_address} не найден в базе")
            await message.answer("❌ Токен не найден.")
            return
        
        try:
            token_name_cleaned = token[2].strip()
            token_address_cleaned = token[1].strip()
            if not token_name_cleaned or not token_address_cleaned:
                if should_log("debug"):
                    logger.debug(f"Очищенные данные токена пустые: name={token_name_cleaned}, address={token_address_cleaned}")
                await message.answer("❌ Токен содержит некорректные данные.")
                return
            token_name_cleaned.encode('utf-8')
            token_address_cleaned.encode('utf-8')
        except UnicodeEncodeError as e:
            if should_log("debug"):
                logger.debug(f"Ошибка кодировки для данных токена: name={token[2]}, address={token[1]}, ошибка={str(e)}")
            await message.answer("❌ Ошибка кодировки данных токена.")
            return
        
        if should_log("debug"):
            logger.debug(f"Найден токен: ID={token[0]}, Адрес={token[1]}, Имя={token[2]}, Тред={token[3]}")
        
        from .keyboards import get_token_control_keyboard
        text = f"Токен: {token_name_cleaned} ({token_address_cleaned[-4:]})"
        if should_log("debug"):
            logger.debug(f"Сформирован текст: {text}")
        
        keyboard = get_token_control_keyboard(token[0])
        if should_log("debug"):
            logger.debug(f"Сформирована клавиатура: {keyboard.inline_keyboard}")
        
        sent_message = await message.answer(text, reply_markup=keyboard)
        await message.delete()
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка обработки команды /edit: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при обработке команды.")

async def get_thread_id_command(message: types.Message):
    if should_log("interface"):
        logger.info(f"Получена команда /get_thread_id от {message.from_user.id}")
    thread_id = message.message_thread_id
    if thread_id:
        await message.answer(f"ID текущей ветки: {thread_id}")
    else:
        await message.answer("❌ Это не ветка чата или ID недоступен.")