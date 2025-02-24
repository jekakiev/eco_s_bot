from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_back_button
from ..states import WalletStates
from database import Database
from utils.logger_config import logger
import aiohttp
import json
from config.settings import ARBISCAN_API_KEY

db = Database()

async def show_test_api_by_hash(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'test_api_by_hash' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Кнопка 'Тест апи (по хешу транзы)' нажата")
    await callback.message.edit_text(
        "📝 Введите хеш транзакции (например, 0x...):",
        reply_markup=get_back_button()
    )
    await state.set_state(WalletStates.waiting_for_transaction_hash)
    await callback.answer()

async def request_transaction_hash(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с хешем транзакции от {message.from_user.id}: {message.text}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
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
                response_text += "=== Логи транзакции (возможные токены и суммы) ===\n"
                for log in logs:
                    response_text += f"Адрес контракта: {log.get('address')}\n"
                    response_text += f"Topics: {log.get('topics')}\n"
                    response_text += f"Data: {log.get('data')}\n\n"
        except json.JSONDecodeError as e:
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
                logger.info(f"Полный JSON-ответ от API (квитанция): {data}")
                if data.get("result"):
                    return str(data["result"])  # Повертаємо сирі JSON-дани квитанції як строку
                else:
                    return "❌ Нет данных о квитанции или произошла ошибка: " + data.get("message", "Нет сообщения об ошибке")
            else:
                return f"❌ Ошибка API: HTTP {response.status}"