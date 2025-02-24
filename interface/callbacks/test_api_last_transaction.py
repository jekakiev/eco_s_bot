from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_wallets_list, get_back_button
from ..states import WalletStates
from database import Database
from utils.logger_config import logger
from utils.arbiscan import get_token_transactions
import aiohttp
from config.settings import ARBISCAN_API_KEY

db = Database()

async def show_test_api(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'test_api_last_transaction' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Кнопка 'Тест апи (последняя транза)' нажата")
    text, reply_markup = get_wallets_list()
    msg = await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await state.update_data(test_api_message_id=msg.message_id)
    await state.set_state(WalletStates.waiting_for_wallet_selection)
    await callback.answer()

async def select_wallet(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'select_wallet' получен от {callback.from_user.id}: {callback.data}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Выбран кошелек: {callback.data}")
    wallet_id = callback.data.replace("select_wallet_", "")
    wallet = db.get_wallet_by_id(wallet_id)
    if not wallet:
        await callback.answer("❌ Кошелек не найден!", show_alert=True)
        return
    transaction_data = await get_latest_transaction(wallet['address'])
    
    # Розділяємо текст на частини по 4000 символів
    chunk_size = 4000
    for i in range(0, len(transaction_data), chunk_size):
        chunk = transaction_data[i:i + chunk_size]
        await callback.message.answer(
            f"📊 Последняя транзакция для кошелька {wallet['name']} ({wallet['address']}):\n\n{chunk}",
            disable_web_page_preview=True
        )
    await callback.message.edit_reply_markup(reply_markup=get_main_menu())
    await state.clear()
    await callback.answer()

async def get_latest_transaction(wallet_address):
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "offset": 1,  # Отримуємо лише одну транзакцію
        "limit": 1,   # Отримуємо лише одну транзакцію
        "apikey": api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "1" and data.get("result"):
                    return str(data["result"][0])  # Повертаємо лише одну останню транзакцію як строку
                else:
                    return "❌ Нет данных о транзакциях или произошла ошибка."
            else:
                return f"❌ Ошибка API: HTTP {response.status}"