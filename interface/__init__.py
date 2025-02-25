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
        wallet_id = message.text.replace("/Editw_", "")
        if not wallet_id.isdigit():
            await message.answer("❌ ID кошелька должен быть числом.")
            return
        wallet_id = int(wallet_id)
        if should_log("debug"):
            logger.debug(f"Попытка найти кошелек с ID: {wallet_id}, полный текст команды: {message.text}")
        # Форсируем повторное подключение к базе, чтобы исключить кэширование или сбой
        db.reconnect()
        if not db.connection or not db.connection.is_connected():
            if should_log("debug"):
                logger.debug("Подключение к базе разорвано, пытаемся переподключиться")
            db.reconnect()
        wallet = db.wallets.get_wallet_by_id(wallet_id)
        if should_log("debug"):
            logger.debug(f"Результат get_wallet_by_id для ID {wallet_id}: {wallet}")
            logger.debug(f"Список кошельков из базы для проверки (после reconnect): {db.wallets.get_all_wallets()}")
        if not wallet:
            if should_log("debug"):
                logger.debug(f"Кошелек с ID {wallet_id} не найден в базе. Список кошельков: {db.wallets.get_all_wallets()}")
            await message.answer("❌ Кошелек не найден.")
            return
        if should_log("debug"):
            logger.debug(f"Кошелек найден: ID={wallet[0]}, Адрес={wallet[1]}, Имя={wallet[2]}, Токены={wallet[3]}")
        from .keyboards import get_wallet_control_keyboard
        text = f"Имя кошелька: {wallet[2]}\nАдрес кошелька: {wallet[1]}"  # wallet[2] — name, wallet[1] — address
        sent_message = await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet[0]))  # wallet[0] — id
        # Удаляем сообщение пользователя с командой
        await message.delete()
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка обработки команды /Editw: {str(e)}", exc_info=True)  # Добавлено exc_info=True для полного стека вызовов
        if should_log("debug"):
            logger.debug(f"Состояние подключения к базе после ошибки: {db.connection.is_connected() if db.connection else 'Нет подключения'}")
        await message.answer("❌ Ошибка при обработке команды.")

async def edit_token_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    if should_log("interface"):
        logger.info(f"Обработка команды /edit для пользователя {message.from_user.id}")
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