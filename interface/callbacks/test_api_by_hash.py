from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_back_button
from ..states import WalletStates
from database import Database
from utils.logger_config import logger
import aiohttp
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
    transaction_data = await get_transaction_by_hash(transaction_hash)
    
    # Логування для діагностики
    logger.info(f"Ответ API для хеша {transaction_hash}: {transaction_data}")
    
    # Розділяємо текст на частини по 4000 символів
    chunk_size = 4000
    for i in range(0, len(transaction_data), chunk_size):
        chunk = transaction_data[i:i + chunk_size]
        await message.answer(
            f"📊 Данные транзакции по хешу {transaction_hash}:\n\n{chunk}",
            disable_web_page_preview=True
        )
    await state.clear()
    await message.answer("🏠 Главное меню:", reply_markup=get_main_menu())

async def get_transaction_by_hash(transaction_hash):
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    params = {
        "module": "proxy",  # Змінено на proxy для action=tx
        "action": "tx",     # Змінено з gettxinfo на tx для отримання деталей транзакції
        "txhash": transaction_hash,
        "apikey": api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Полный JSON-ответ от API: {data}")  # Додаткове логування для діагностики
                if data.get("status") == "1" and data.get("result"):
                    return str(data["result"])  # Повертаємо сирі JSON-дани як строку
                else:
                    return "❌ Нет данных о транзакции или произошла ошибка: " + data.get("message", "Нет сообщения об ошибке")
            else:
                return f"❌ Ошибка API: HTTP {response.status}"