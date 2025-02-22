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
    dp.message.register(edit_wallet_command, Command(commands=[f"Edit_{wallet['address'][-4:]}" for wallet in db.get_all_wallets()]))

# Обработчик команды для редактирования кошельков
async def edit_wallet_command(message: types.Message):
    logger.info(f"Получена команда: {message.text}")
    try:
        short_address = message.text.split("_")[1]
        logger.info(f"Извлечен короткий адрес: {short_address}")

        wallets = db.get_all_wallets()
        wallet = next((w for w in wallets if w["address"].endswith(short_address)), None)
        
        if not wallet:
            logger.warning(f"Кошелек с адресом, заканчивающимся на {short_address}, не найден")
            await message.answer("❌ Кошелек не найден.")
            return

        logger.info(f"Найден кошелек: {wallet['name']} ({wallet['address']})")
        text = f"Имя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
        await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet['id']))
        logger.info(f"Отправлено меню редактирования для кошелька {wallet['name']}")

    except Exception as e:
        logger.error(f"Ошибка обработки команды /Edit: {str(e)}")
        await message.answer("❌ Ошибка при обработке команды. Проверьте логи.")