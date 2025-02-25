from aiogram import types
from database import Database
from .keyboards import get_main_menu, get_back_button, get_wallets_list, get_wallet_control_keyboard, get_tokens_keyboard, get_tracked_tokens_list, get_token_control_keyboard, get_token_name_confirmation_keyboard, get_thread_confirmation_keyboard, get_commands_list, get_settings_list, get_interval_edit_keyboard
from .handlers import register_handlers
from utils.logger_config import logger, should_log

db = Database()

async def edit_wallet_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    if should_log("interface"):
        logger.info(f"Обработка команды /Edit для пользователя {message.from_user.id}")
    try:
        short_address = message.text.split("_")[1]
        wallets = db.wallets.get_all_wallets()  # Отримуємо кортежі
        if should_log("debug"):
            logger.debug(f"Список кошельков из базы: {wallets}")
        wallet = next((w for w in wallets if w[1].endswith(short_address)), None)  # w[1] — address
        if not wallet:
            if should_log("debug"):
                logger.debug(f"Кошелек с последними 4 символами {short_address} не найден в базе: {wallets}")
            await message.answer("❌ Кошелек не найден.")
            return
        from .keyboards import get_wallet_control_keyboard
        text = f"Имя кошелька: {wallet[2]}\nАдрес кошелька: {wallet[1]}"  # wallet[2] — name, wallet[1] — address
        await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet[0]))  # wallet[0] — id
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка обработки команды /Edit: {str(e)}")
        await message.answer("❌ Ошибка при обработке команды.")

async def edit_token_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    if should_log("interface"):
        logger.info(f"Обработка команды /edit для пользователя {message.from_user.id}")
    try:
        short_address = message.text.split("_")[1]
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
        await message.answer(text, reply_markup=get_token_control_keyboard(token[0]))  # token[0] — id
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка обработки команды /edit: {str(e)}")
        await message.answer("❌ Ошибка при обработке команды.")