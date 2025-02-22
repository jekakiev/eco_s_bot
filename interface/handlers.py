from aiogram import Dispatcher, F, types
from .callbacks import (
    show_wallets, add_wallet_start, process_wallet_address, process_wallet_name,
    toggle_token, confirm_tokens, delete_wallet, rename_wallet_start, process_new_wallet_name,
    go_home
)
from aiogram.filters import Command
from .states import WalletStates
from database import Database
from logger_config import logger
from interface import get_wallet_control_keyboard
from settings import LOG_SUCCESSFUL_TRANSACTIONS

db = Database()

# === РЕЄСТРАЦІЯ ОБРОБНИКІВ ===
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
    dp.callback_query.register(go_home, F.data == "home")
    dp.message.register(edit_wallet_command, Command("Edit"))  # Реєстрація команди Edit

# Обробник команди для редагування гаманців
async def edit_wallet_command(message: types.Message):
    logger.info(f"Отримано команду: {message.text}")
    try:
        # Перевірка формату команди
        if "_" not in message.text:
            logger.warning("Команда не містить символу '_'")
            await message.answer("❌ Неправильний формат команди. Використовуйте /Edit_КОРОТКИЙ_АДРЕС (наприклад, /Edit_9A7f)")
            return
        
        # Видобуття короткого адреси
        short_address = message.text.split("_")[1]
        logger.info(f"Отримано короткий адрес: {short_address}")

        # Отримання всіх гаманців з бази даних
        wallets = db.get_all_wallets()
        logger.info(f"Гаманці: {wallets}")

        # Пошук гаманця за коротким адресом
        wallet = next((wallet for wallet in wallets if wallet["address"].endswith(short_address)), None)
        if not wallet:
            logger.warning(f"Гаманець з адресою, що закінчується на {short_address}, не знайдено.")
            await message.answer("❌ Гаманець не знайдено.")
            return

        # Надсилання інформації про гаманець і клавіатури для управління
        logger.info(f"Знайдено гаманець: {wallet['name']} з адресою {wallet['address']}")
        text = f"Ім’я гаманця: {wallet['name']}\nАдреса гаманця: {wallet['address']}"
        await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet['id']))
        logger.info("Надіслано меню редагування")
    except Exception as e:
        logger.error(f"Помилка обробки команди Edit: {str(e)}")
        await message.answer("❌ Сталася помилка при обробці команди.")