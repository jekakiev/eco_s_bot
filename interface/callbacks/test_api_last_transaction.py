# /interface/callbacks/test_api_last_transaction.py
from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_wallet_selection_keyboard  # Заменяем get_wallets_list
from ..states import WalletStates
from app_config import db
from utils.logger_config import logger, should_log
from utils.arbiscan import get_token_transactions
import aiohttp
from config.settings import ARBISCAN_API_KEY

async def show_test_api(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'test_api_last_transaction' получен от {callback.from_user.id}")
        logger.info("Кнопка 'Тест апи (последняя транза)' нажата")
    text, reply_markup = get_wallet_selection_keyboard()  # Используем новую функцию
    msg = await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await state.update_data(test_api_message_id=msg.message_id)
    await state.set_state(WalletStates.waiting_for_wallet_selection)
    await callback.answer()

async def select_wallet(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'select_wallet' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Выбран кошелек: {callback.data}")
    wallet_id = callback.data.replace("select_wallet_", "")
    wallet = db.wallets.get_wallet_by_id(wallet_id)
    if not wallet:
        await callback.answer("❌ Кошелек не найден!", show_alert=True)
        return
    
    # Получение данных из состояния
    state_data = await state.get_data()
    message_id = state_data.get("test_api_message_id")
    
    # Отримання найновішої транзакції для хеша та посилання
    latest_tx = await get_latest_transaction(wallet[1])
    swap_tx_data = await get_latest_swap_transaction(wallet[1])
    
    # Надсилаємо дані про своп-транзакцію (якщо є)
    swap_tx_str = str(swap_tx_data)
    if swap_tx_str.startswith("❌"):
        await callback.message.answer(swap_tx_str, disable_web_page_preview=True)
    else:
        chunk_size = 4000
        for i in range(0, len(swap_tx_str), chunk_size):
            chunk = swap_tx_str[i:i + chunk_size]
            await callback.message.answer(
                f"📊 Последняя своп-транзакция для кошелька {wallet[2]} ({wallet[1]}):\n\n{chunk}",
                disable_web_page_preview=True
            )
    
    # Надсилаємо хеш найновішої транзакції з посиланням
    if isinstance(latest_tx, str) and latest_tx.startswith("❌"):
        await callback.message.answer(f"❗ Ошибка получения последней транзакции: {latest_tx}", disable_web_page_preview=True)
    else:
        tx_hash = latest_tx.get("hash", "Неизвестно")
        tx_link = f"https://arbiscan.io/tx/{tx_hash}"
        await callback.message.answer(
            f"🔗 Хеш последной транзакции: {tx_hash}\nПосмотреть на Arbiscan: {tx_link}",
            disable_web_page_preview=True
        )
    
    # Обновляем исходное сообщение с кнопками главного меню
    if message_id:
        await callback.message.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=message_id,
            reply_markup=get_main_menu()
        )
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
        "limit": 1,
        "apikey": api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "1" and data.get("result"):
                    if should_log("debug"):
                        logger.debug(f"Получена последняя транзакция для {wallet_address}: {data['result'][0]}")
                    return data["result"][0]
                else:
                    if should_log("api_errors"):
                        logger.error("Нет данных о транзакциях или произошла ошибка в ответе Arbiscan")
                    return "❌ Нет данных о транзакциях или произошла ошибка."
            else:
                if should_log("api_errors"):
                    logger.error(f"Ошибка API Arbiscan: HTTP {response.status}")
                return f"❌ Ошибка API: HTTP {response.status}"

async def get_latest_swap_transaction(wallet_address):
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    swap_method_ids = [
        "0x38ed1739", "0x7ff36ab5", "0x022c0d9f", "0x0298adcd", "0x8803dbee", "0x1fff991f"
    ]
    dex_router_addresses = [
        "0xE592427A0AEce92De3Edee1F18E0157C05861564", "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506", "0xb254ee265261675528bddb0796741c0c65a4c158"
    ]
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "limit": 100,
        "apikey": api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "1" and data.get("result"):
                    for transaction in data["result"]:
                        to_address = transaction.get("to", "").lower()
                        method_id = transaction.get("methodId", "").lower()
                        if should_log("debug"):
                            logger.debug(f"Проверяем транзакцию: to={to_address}, methodId={method_id}, hash={transaction.get('hash', 'Неизвестно')}")
                        if (to_address in [addr.lower() for addr in dex_router_addresses] and 
                            method_id in [mid.lower() for mid in swap_method_ids]):
                            if should_log("debug"):
                                logger.debug(f"Найдена своп-транзакция: {transaction}")
                            return str(transaction)
                    if should_log("api_errors"):
                        logger.warning("Нет данных о своп-транзакциях.")
                    return "❌ Нет данных о своп-транзакциях."
                else:
                    if should_log("api_errors"):
                        logger.error("Нет данных о транзакциях или произошла ошибка в ответе Arbiscan")
                    return "❌ Нет данных о транзакциях или произошла ошибка."
            else:
                if should_log("api_errors"):
                    logger.error(f"Ошибка API Arbiscan: HTTP {response.status}")
                return f"❌ Ошибка API: HTTP {response.status}"