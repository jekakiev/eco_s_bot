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

# === РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ===
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
    dp.message.register(edit_wallet_command, Command("Edit"))  # Регистрация команды Edit

# Обработчик команды для редактирования кошельков
async def edit_wallet_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        # Проверка формата команды
        if "_" not in message.text:
            logger.warning("Команда не содержит символа '_'")
            await message.answer("❌ Неверный формат команды. Используйте /Edit_КОРОТКИЙ_АДРЕС")
            return
        
        # Извлечение короткого адреса
        short_address = message.text.split("_")[1]
        logger.info(f"Получен короткий адрес: {short_address}")

        # Получение всех кошельков из базы данных
        wallets = db.get_all_wallets()
        logger.info(f"Wallets: {wallets}")

        # Поиск кошелька по короткому адресу
        wallet = next((wallet for wallet in wallets if wallet["address"].endswith(short_address)), None)
        if not wallet:
            logger.warning(f"Кошелек с адресом, оканчивающимся на {short_address}, не найден.")
            await message.answer("❌ Кошелек не найден.")
            return

        # Отправка информации о кошельке и клавиатуры для управления
        logger.info(f"Найден кошелек: {wallet['name']} с адресом {wallet['address']}")
        text = f"Имя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
        await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet['id']))
        logger.info("Отправлено меню редактирования")
    except Exception as e:
        logger.error(f"Ошибка обработки команды Edit: {e}")
        await message.answer("❌ Произошла ошибка при обработке команды.")