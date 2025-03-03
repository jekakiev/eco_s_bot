# /app/bot.py
import asyncio
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from interface.handlers import register_handlers, edit_wallet_command
from interface.keyboards import get_main_menu
from config.settings import BOT_TOKEN, CHAT_ID
from config.bot_instance import bot
from utils.logger_config import logger, update_log_settings, should_log
from transaction_manager import start_transaction_monitoring
from app_config import db
from flask import Flask, request, jsonify
import os

# Ініціалізація Flask
app = Flask(__name__)

# Ініціалізація Aiogram
dp = Dispatcher(storage=MemoryStorage())

# Flask-ендпоінт для вебхука Moralis Streams
@app.route('/webhook', methods=['POST'])
def webhook():
    if should_log("transaction"):
        logger.info("Отримано POST-запит від Moralis Streams на /webhook")
    data = request.get_json()
    if not data:
        logger.error("Отримано порожній вебхук-запит")
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    if should_log("debug"):
        logger.debug(f"Дані вебхука: {data}")
    
    # Обробка даних від Moralis (асинхронно відправляємо повідомлення)
    try:
        tx_hash = data.get("txs", [{}])[0].get("hash", "невідомий хеш")
        message = f"Нова транзакція виявлена!\nХеш: `{tx_hash}`"
        asyncio.run_coroutine_threadsafe(bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown"), asyncio.get_event_loop())
        logger.info(f"Повідомлення про транзакцію відправлено: {tx_hash}")
    except Exception as e:
        logger.error(f"Помилка при обробці вебхука: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "success"}), 200

def run_flask():
    """Запуск Flask-сервера у фоновому потоці."""
    port = int(os.getenv("PORT", 8080))  # Беремо порт із змінної оточення або 8080 за замовчуванням
    logger.info(f"Запуск Flask-сервера на порту {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if should_log("interface"):
    logger.info("Регистрация обработчиков")
register_handlers(dp)
if should_log("interface"):
    logger.info("Обработчики зарегистрированы")

# Регистрируем команду /Editw_<wallet_id> динамически
@dp.message(lambda message: message.text and message.text.startswith("/Editw_"))
async def dynamic_edit_wallet_command(message: types.Message):
    if should_log("interface"):
        logger.info(f"Динамическая команда /Editw_ получена от {message.from_user.id}: {message.text}")
        logger.info(f"Обработка динамической команды /Editw_ для пользователя {message.from_user.id}")
    await edit_wallet_command(message)

@dp.message(Command("start"))
async def start_command(message):
    if should_log("interface"):
        logger.info(f"Команда /start получена от {message.from_user.id}")
        logger.info(f"Команда /start обработана для пользователя {message.from_user.id}")
    menu = get_main_menu()
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=menu)

@dp.message(Command("get_last_transaction"))
async def get_last_transaction_command(message):
    if should_log("interface"):
        logger.info(f"Команда /get_last_transaction получена от {message.from_user.id}")
        logger.info(f"Команда /get_last_transaction обработана для пользователя {message.from_user.id}")
    await message.answer("Функция в разработке!")

@dp.message(Command("get_thread_id"))
async def get_thread_id_command(message):
    if should_log("interface"):
        logger.info(f"Команда /get_thread_id получена от {message.from_user.id}")
        logger.info(f"Команда /get_thread_id обработана для пользователя {message.from_user.id}")
    thread_id = message.message_thread_id if message.is_topic_message else "Нет треда"
    await message.answer(f"ID текущего треда: `{thread_id}`", parse_mode="Markdown")

async def main():
    if should_log("interface"):
        logger.info("🚀 Бот запущен и ждет новые транзакции!")
    
    # Запускаємо Flask у фоновому потоці
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаємо моніторинг транзакцій і Aiogram polling у головному циклі asyncio
    await asyncio.gather(
        start_transaction_monitoring(bot, CHAT_ID),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())