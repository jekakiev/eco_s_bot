from aiogram import types
from database import Database
from .keyboards import get_main_menu, get_back_button, get_wallets_list, get_wallet_control_keyboard, get_tokens_keyboard, get_tracked_tokens_list, get_token_control_keyboard, get_token_name_confirmation_keyboard, get_thread_confirmation_keyboard, get_commands_list, get_settings_list, get_interval_edit_keyboard
from .handlers import register_handlers
from utils.logger_config import logger, should_log

db = Database()

async def edit_wallet_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    if should_log("interface"):
        logger.info(f"Обработка команды /Editw для пользователя {message.from_user.id}")
    try:
        if not message.text.startswith("/Editw_"):
            await message.answer("❌ Неверный формат команды. Используйте /Editw_<ID_кошелька>.")
            return
        wallet_id_str = message.text.replace("/Editw_", "")
        if not wallet_id_str.isdigit():
            await message.answer("❌ ID кошелька должен быть числом.")
            return
        wallet_id = int(wallet_id_str)
        if should_log("debug"):
            logger.debug(f"Попытка найти кошелек с ID: {wallet_id}, полный текст команды: {message.text}")
        # Форсируем повторное подключение к базе, чтобы исключить кэширование или сбой
        db.reconnect()
        if not db.connection or not db.connection.is_connected():
            if should_log("debug"):
                logger.debug("Подключение к базе разорвано, пытаемся переподключиться")
            db.reconnect()
        
        # Поиск по ID
        wallet = db.wallets.get_wallet_by_id(wallet_id)
        if not wallet:
            if should_log("debug"):
                logger.debug(f"Кошелек с ID {wallet_id} не найден. Проверка всех записей: {db.wallets.get_all_wallets()}")
            # Альтернативный поиск по последним 4 символам адреса, как для токенов
            wallets = db.wallets.get_all_wallets()
            wallet_by_short = next((w for w in wallets if w[1].endswith(wallet_id_str)), None)  # w[1] — address
            if wallet_by_short:
                wallet = wallet_by_short
                wallet_id = wallet[0]  # Обновляем wallet_id на найденный
                if should_log("debug"):
                    logger.debug(f"Кошелек найден по последним 4 символами адреса: ID={wallet[0]}, Адрес={wallet[1]}")
            else:
                if should_log("debug"):
                    logger.debug(f"Кошелек с ID или последними 4 символами {wallet_id_str} не найден в базе.")
                await message.answer("❌ Кошелек не найден.")
                return
        
        if should_log("debug"):
            logger.debug(f"Результат get_wallet_by_id для ID {wallet_id}: {wallet}")
            logger.debug(f"Список кошельков из базы для проверки (после reconnect): {db.wallets.get_all_wallets()}")
        
        # Проверка на корректность данных
        if not all(wallet) or not wallet[1] or not wallet[2]:  # Проверяем, что address и name не пустые
            if should_log("debug"):
                logger.debug(f"Некорректные данные для кошелька с ID {wallet_id}: {wallet}")
            await message.answer("❌ Кошелек содержит некорректные данные.")
            return
        
        if should_log("debug"):
            logger.debug(f"Кошелек найден: ID={wallet[0]}, Адрес={wallet[1]}, Имя={wallet[2]}, Токены={wallet[3]}")
        
        from .keyboards import get_wallet_control_keyboard
        try:
            text = f"Имя кошелька: {wallet[2]}\nАдрес кошелька: {wallet[1]}"  # wallet[2] — name, wallet[1] — address
            if should_log("debug"):
                logger.debug(f"Сформирован текст сообщения для кошелька ID {wallet_id}: {text}")
            keyboard = get_wallet_control_keyboard(wallet[0])  # wallet[0] — id
            if should_log("debug"):
                logger.debug(f"Сформирована клавиатура для кошелька ID {wallet_id}: {keyboard.inline_keyboard}")
            sent_message = await message.answer(text, reply_markup=keyboard)
        except Exception as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка при отправке сообщения для кошелька ID {wallet_id}: {str(e)}", exc_info=True)
            await message.answer("❌ Ошибка при отправке данных кошелька.")
            return
        
        # Удаляем сообщение пользователя с командой
        await message.delete()
    
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка обработки команды /Editw: {str(e)}", exc_info=True)  # Убедимся, что логируем полный стек вызовов
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
        if should_log("api_errors"):
            logger.error(f"Ошибка обработки команды /edit: {str(e)}", exc_info=True)  # Добавлено exc_info=True для полного стека вызовов
        await message.answer("❌ Ошибка при обработке команды.")