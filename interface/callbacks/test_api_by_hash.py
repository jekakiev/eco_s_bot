# /interface/callbacks/test_api_by_hash.py
from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_back_button
from ..states import WalletStates
from app_config import db
from utils.logger_config import logger, should_log
import aiohttp
import json
from config.settings import ARBISCAN_API_KEY
from utils.arbiscan import get_token_info

async def show_test_api_by_hash(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'test_api_by_hash' получен от {callback.from_user.id}")
        logger.info("Кнопка 'Тест апи (по хешу транзы)' нажата")
    await callback.message.edit_text(
        "📝 Введите хеш транзакции (например, 0x...):",
        reply_markup=get_back_button()
    )
    await state.set_state(WalletStates.waiting_for_transaction_hash)
    await callback.answer()

async def request_transaction_hash(message: types.Message, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Сообщение с хешем транзакции от {message.from_user.id}: {message.text}")
        logger.info(f"Введен хеш транзакции: {message.text}")
    transaction_hash = message.text.strip()
    if not transaction_hash.startswith("0x") or len(transaction_hash) != 66:
        await message.answer("❌ Неверный формат хеша транзакции. Введите хеш в формате 0x... (64 символа после 0x).", reply_markup=get_back_button())
        return
    
    transaction_data = await get_transaction_by_hash(transaction_hash)
    receipt_data = await get_transaction_receipt(transaction_hash)
    
    if should_log("debug"):
        logger.debug(f"Ответ API для хеша {transaction_hash} (транзакция): {transaction_data}")
        logger.debug(f"Ответ API для хеша {transaction_hash} (квитанция): {receipt_data}")
    
    response_text = f"📊 Данные транзакции по хешу {transaction_hash}:\n\n"
    response_text += "=== Детали транзакции ===\n"
    response_text += str(transaction_data) + "\n\n"
    
    if not receipt_data.startswith("❌"):
        response_text += "=== Квитанция и логи транзакции ===\n"
        response_text += str(receipt_data) + "\n\n"
    
    if not receipt_data.startswith("❌"):
        try:
            receipt = json.loads(receipt_data.replace("'", '"'))
            logs = receipt.get("logs", [])
            if logs:
                response_text += "=== Возможные токены и суммы из логів ===\n"
                for log in logs:
                    address = log.get("address", "Неизвестно")
                    topics = log.get("topics", [])
                    data = log.get("data", "0x")
                    
                    if topics and topics[0] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                        sender = topics[1][26:] if len(topics) > 1 else "Неизвестно"
                        recipient = topics[2][26:] if len(topics) > 2 else "Неизвестно"
                        amount_hex = data[2:]
                        try:
                            amount = int(amount_hex, 16)
                            token_info = await get_token_info(address)
                            decimals = int(token_info.get("tokenDecimal", 18))
                            human_readable_amount = amount / (10 ** decimals)
                            response_text += f"Transfer: Адрес токена: {address}\n"
                            response_text += f"Отправитель: {sender}\n"
                            response_text += f"Получатель: {recipient}\n"
                            response_text += f"Сумма: {human_readable_amount} (предполагается {decimals} знаков)\n\n"
                        except ValueError as e:
                            if should_log("api_errors"):
                                logger.error(f"Ошибка декодирования суммы: {str(e)}")
                            response_text += f"Ошибка декодирования суммы для {address}\n\n"
                    
                    elif topics and topics[0] == "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822":
                        token0 = topics[1][26:] if len(topics) > 1 else "Неизвестно"
                        token1 = topics[2][26:] if len(topics) > 2 else "Неизвестно"
                        if len(data) >= 66:
                            amount0_hex = data[2:66]
                            amount1_hex = data[66:130]
                            try:
                                amount0 = int(amount0_hex, 16)
                                amount1 = int(amount1_hex, 16)
                                token0_info = await get_token_info(token0)
                                token1_info = await get_token_info(token1)
                                decimals0 = int(token0_info.get("tokenDecimal", 18))
                                decimals1 = int(token1_info.get("tokenDecimal", 18))
                                human_readable_amount0 = amount0 / (10 ** decimals0)
                                human_readable_amount1 = amount1 / (10 ** decimals1)
                                response_text += f"Swap: Пул Uniswap: {address}\n"
                                response_text += f"Токен 1: {token0}\n"
                                response_text += f"Токен 2: {token1}\n"
                                response_text += f"Сумма токена 1: {human_readable_amount0} (предполагается {decimals0} знаков)\n"
                                response_text += f"Сумма токена 2: {human_readable_amount1} (предполагается {decimals1} знаков)\n\n"
                            except ValueError as e:
                                if should_log("api_errors"):
                                    logger.error(f"Ошибка декодирования суммы свопа: {str(e)}")
                                response_text += f"Ошибка декодирования суммы свопа для {address}\n\n"
        except json.JSONDecodeError as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка декодирования JSON логов: {str(e)}")
            response_text += "❗ Ошибка при обработке логів.\n\n"
    
    chunk_size = 4000
    for i in range(0, len(response_text), chunk_size):
        chunk = response_text[i:i + chunk_size]
        await message.answer(chunk, disable_web_page_preview=True)
    
    await state.clear()
    await message.answer("🏠 Главное меню:", reply_markup=get_main_menu())

async def get_transaction_by_hash(transaction_hash):
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    params = {
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": transaction_hash,
        "apikey": api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if should_log("debug"):
                    logger.debug(f"Полный JSON-ответ от API (транзакция): {data}")
                if data.get("result"):
                    return str(data["result"])
                else:
                    if should_log("api_errors"):
                        logger.error(f"Нет данных о транзакции или произошла ошибка: {data.get('message', 'Нет сообщения об ошибке')}")
                    return "❌ Нет данных о транзакции или произошла ошибка: " + data.get("message", "Нет сообщения об ошибке")
            else:
                if should_log("api_errors"):
                    logger.error(f"Ошибка API Arbiscan: HTTP {response.status}")
                return f"❌ Ошибка API: HTTP {response.status}"

async def get_transaction_receipt(transaction_hash):
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    params = {
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": transaction_hash,
        "apikey": api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if should_log("debug"):
                    logger.debug(f"Полный JSON-ответ от API (квитанция): {data}")
                if data.get("result"):
                    return str(data["result"])
                else:
                    if should_log("api_errors"):
                        logger.error(f"Нет данных о квитанции или произошла ошибка: {data.get('message', 'Нет сообщения об ошибке')}")
                    return "❌ Нет данных о квитанции или произошла ошибка: " + data.get("message", "Нет сообщения об ошибке")
            else:
                if should_log("api_errors"):
                    logger.error(f"Ошибка API Arbiscan: HTTP {response.status}")
                return f"❌ Ошибка API: HTTP {response.status}"