from aiogram import types
from database import Database
from .keyboards import get_main_menu, get_back_button, get_wallets_list, get_wallet_control_keyboard, get_tokens_keyboard, get_tracked_tokens_list, get_token_control_keyboard, get_token_name_confirmation_keyboard, get_thread_confirmation_keyboard, get_commands_list, get_settings_list, get_interval_edit_keyboard
from .handlers import register_handlers
from utils.logger_config import logger, should_log

db = Database()

async def edit_wallet_command(message: types.Message):
    logger.info(f"Получена команда: /Editw_68B8 от пользователя {message.from_user.id}")
    if should_log("interface"):
        logger.info(f"Обработка команды /Editw для пользователя {message.from_user.id}")
    try:
        if not message.text.startswith("/Editw_"):
            await message.answer("❌ Неверный формат команды. Используйте /Editw_XXXX (последние 4 символа адреса кошелька).")
            return
        short_address = message.text.replace("/Editw_", "")
        if len(short_address) != 4:
            await message.answer("❌ Последние 4 символа адреса должны быть указаны (например, /Editw_68B8).")
            return
        if should_log("debug"):
            logger.debug(f"Попытка найти кошелек с последними 4 символами адреса: {short_address}")
        
        # Простое подключение к базе
        db.reconnect()
        
        # Поиск по последним 4 символам адреса
        wallets = db.wallets.get_all_wallets()
        if should_log("debug"):
            logger.debug(f"Список кошельков из базы: {wallets}")
        wallet = next((w for w in wallets if w[1].endswith(short_address)), None)  # w[1] — address
        if not wallet:
            if should_log("debug"):
                logger.debug(f"Кошелек с последними 4 символами {short_address} не найден в базе")
            await message.answer("❌ Кошелек не найден.")
            return
        
        # Проверка данных на скрытые символы и кодировку
        try:
            name_cleaned = wallet[2].strip()  # Удаляем пробелы и табуляции
            address_cleaned = wallet[1].strip()
            if not name_cleaned or not address_cleaned:
                if should_log("debug"):
                    logger.debug(f"Очищенные данные пустые: name={name_cleaned}, address={address_cleaned}")
                await message.answer("❌ Кошелек содержит некорректные данные.")
                return
            name_cleaned.encode('utf-8')  # Проверяем кодировку
            address_cleaned.encode('utf-8')
        except UnicodeEncodeError as e:
            if should_log("debug"):
                logger.debug(f"Ошибка кодировки для данных кошелька: name={wallet[2]}, address={wallet[1]}, ошибка={str(e)}")
            await message.answer("❌ Ошибка кодировки данных кошелька.")
            return
        
        if should_log("debug"):
            logger.debug(f"Найден кошелек: ID={wallet[0]}, Адрес={wallet[1]}, Имя={wallet[2]}, Токены={wallet[3]}")
        
        from .keyboards import get_wallet_control_keyboard
        try:
            # Упрощённый текст, идентичный токенам
            text = f"Кошелек: {name_cleaned} ({address_cleaned[-4:]})"
            if should_log("debug"):
                logger.debug(f"Сформирован текст: {text}")
            
            keyboard = get_wallet_control_keyboard(wallet[0])  # wallet[0] — id
            if should_log("debug"):
                logger.debug(f"Сформирована клавиатура: {keyboard.inline_keyboard}")
            
            sent_message = await message.answer(text, reply_markup=keyboard)
            await message.delete()
        except Exception as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка при отправке сообщения для кошелька с адресом {address_cleaned[-4:]}: {str(e)}", exc_info=True)
            await message.answer("❌ Ошибка при отправке данных кошелька.")
            return
    
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка обработки команды /Editw: {str(e)}", exc_info=True)
        if should_log("debug"):
            logger.debug(f"Состояние подключения к базе: {db.connection.is_connected() if db.connection else 'Нет подключения'}")
            logger.debug(f"Список кошельков: {db.wallets.get_all_wallets()}")
        await message.answer("❌ Ошибка при обработке команды.")

async def edit_token_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        short_address = message.text.split("_")[1]
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
        
        # Проверка данных на скрытые символы и кодировку
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