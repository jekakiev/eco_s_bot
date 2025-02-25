from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_back_button
from ..states import WalletStates
from app_config import db  # Імпортуємо db з app_config
from utils.logger_config import logger, should_log
import aiohttp
import json
from config.settings import ARBISCAN_API_KEY
from utils.arbiscan import get_token_info

db = Database()

async def show_test_api_by_hash(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'test_api_by_hash' получен от {callback.from_user.id}")
    if should_log("interface"):
        logger.info("Кнопка 'Тест апи (по хешу транзы)' нажата")
    await callback.message.edit_text(
        "📝 Введите хеш транзакции (например, 0x...):",
        reply_markup=get_back_button()
    )
    await state.set_state(WalletStates.waiting_for_transaction_hash)
    await callback.answer()

async def request_transaction_hash(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с хешем транзакции от {message.from_user.id}: {message.text}")
    if should_log("interface"):
        logger.info(f"Введен хеш транзакции: {message.text}")
    transaction_hash = message.text.strip()
    if not transaction_hash.startswith("0x") or len(transaction_hash) != 66:  # Перевірка формату хеша (0x + 64 символи)
        await message.answer("❌ Неверный формат хеша транзакции. Введите хеш в формате 0x... (64 символа после 0x).", reply_markup=get_back_button())
        return
    
    # Отримання деталей транзакції
    transaction_data = await get_transaction_by_hash(transaction_hash)
    # Отримання квитанції транзакції для логів
    receipt_data = await get_transaction_receipt(transaction_hash)
    
    # Логування для діагностики
    if should_log("debug"):
        logger.info(f"Ответ API для хеша {transaction_hash} (транзакция): {transaction_data}")
        logger.info(f"Ответ API для хеша {transaction_hash} (квитанция): {receipt_data}")
    
    # Формуємо текст для відправки
    response_text = f"📊 Данные транзакции по хешу {transaction_hash}:\n\n"
    
    # Додаємо дані про саму транзакцію
    response_text += "=== Детали транзакции ===\n"
    response_text += str(transaction_data) + "\n\n"
    
    # Додаємо дані про квитанцію (логи, якщо є)
    if not receipt_data.startswith("❌"):
        response_text += "=== Квитанция и логи транзакции ===\n"
        response_text += str(receipt_data) + "\n\n"
    
    # Спробуємо витягти дані про токени і суми з логів (якщо є)
    if not receipt_data.startswith("❌"):
        try:
            receipt = json.loads(receipt_data.replace("'", '"'))  # Конвертуємо рядок у словник
            logs = receipt.get("logs", [])
            if logs:
                response_text += "=== Возможные токены и суммы из логів ===\n"
                for log in logs:
                    address = log.get("address", "Неизвестно")
                    topics = log.get("topics", [])
                    data = log.get("data", "0x")
                    
                    # Перевіряємо, чи це подія Transfer
                    if topics and topics[0] == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                        # Витягуємо відправника і отримувача з topics
                        sender = topics[1][26:] if len(topics) > 1 else "Неизвестно"  # Останні 20 байт (адреса)
                        recipient = topics[2][26:] if len(topics) > 2 else "Неизвестно"
                        # Конвертуємо суму з data (припускаємо uint256)
                        amount_hex = data[2:]  # Видаляємо "0x"
                        try:
                            amount = int(amount_hex, 16)  # Конвертуємо в десятковий
                            token_info = await get_token_info(address)  # Отримання decimals через API
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
                    
                    # Перевіряємо, чи це подія Swap (Uniswap V2/V3)
                    elif topics and topics[0] == "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822":
                        # Витягуємо токени з topics (припускаємо, що це Uniswap V2/V3)
                        token0 = topics[1][26:] if len(topics) > 1 else "Неизвестно"
                        token1 = topics[2][26:] if len(topics) > 2 else "Неизвестно"
                        # Конвертуємо суми з data (припускаємо, що data має 2 uint256 для amount0 и amount1)
                        if len(data) >= 66:  # Перевіряємо, чи є достатньо даних
                            amount0_hex = data[2:66]  # Первые 32 байта
                            amount1_hex = data[66:130]  # Следующие 32 байта
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
    
    # Розділяємо текст на частини по 4000 символів
    chunk_size = 4000
    for i in range(0, len(response_text), chunk_size):
        chunk = response_text[i:i + chunk_size]
        await message.answer(
            chunk,
            disable_web_page_preview=True
        )
    
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
                    logger.info(f"Полный JSON-ответ от API (транзакция): {data}")
                if data.get("result"):
                    return str(data["result"])  # Повертаємо сирі JSON-дани як строку
                else:
                    return "❌ Нет данных о транзакции или произошла ошибка: " + data.get("message", "Нет сообщения об ошибке")
            else:
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
                    logger.info(f"Полный JSON-ответ от API (квитанция): {data}")
                if data.get("result"):
                    return str(data["result"])  # Повертаємо сирі JSON-дани квитанції як строку
                else:
                    return "❌ Нет данных о квитанции или произошла ошибка: " + data.get("message", "Нет сообщения об ошибке")
            else:
                return f"❌ Ошибка API: HTTP {response.status}"