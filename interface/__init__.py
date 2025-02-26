from aiogram import types
from db import Database
from .keyboards import get_main_menu, get_back_button, get_wallets_list, get_wallet_control_keyboard, get_tokens_keyboard, get_tracked_tokens_list, get_token_control_keyboard, get_token_name_confirmation_keyboard, get_thread_confirmation_keyboard, get_commands_list, get_settings_list, get_interval_edit_keyboard
from .handlers import register_handlers
from utils.logger_config import logger, should_log

db = Database()

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