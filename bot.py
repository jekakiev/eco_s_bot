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

if should_log("interface"):
    logger.info("Регистрация обработчиков")
register_handlers(dp)
if should_log("interface"):
    logger.info("Обработчики зарегистрированы")

# Регистрируем команду /Editw_<wallet_id> динамически
@dp.message(lambda message: message.text and message.text.startswith("/Editw_"))
async def dynamic_edit_wallet_command(message: types.Message):
    if should_log("interface"):
        logger.info(f"Динамическая команда /Editw_ отримана від {message.from_user.id}: {message.text}")
        logger.info(f"Обробка динамічної команди /Editw_ для користувача {message.from_user.id}")
    await edit_wallet_command(message)

@dp.message(Command("start"))
async def start_command(message):
    if should_log("interface"):
        logger.info(f"Команда /start отримана від {message.from_user.id}")
        logger.info(f"Команда /start оброблена для користувача {message.from_user.id}")
    menu = get_main_menu()
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=menu)

@dp.message(Command("get_last_transaction"))
async def get_last_transaction_command(message):
    if should_log("interface"):
        logger.info(f"Команда /get_last_transaction отримана від {message.from_user.id}")
        logger.info(f"Команда /get_last_transaction оброблена для користувача {message.from_user.id}")
    await message.answer("Функція в розробці!")

@dp.message(Command("get_thread_id"))
async def get_thread_id_command(message):
    if should_log("interface"):
        logger.info(f"Команда /get_thread_id отримана від {message.from_user.id}")
        logger.info(f"Команда /get_thread_id оброблена для користувача {message.from_user.id}")
    thread_id = message.message_thread_id if message.is_topic_message else "Немає треда"
    await message.answer(f"ID поточного треда: `{thread_id}`", parse_mode="Markdown")

async def run_aiogram():
    """Запуск Aiogram polling і моніторингу транзакцій."""
    if should_log("interface"):
        logger.info("Запуск Aiogram polling і моніторингу транзакцій")
    await asyncio.gather(
        start_transaction_monitoring(bot, CHAT_ID),
        dp.start_polling(bot)
    )

# Запускаємо Aiogram у фоновому потоці при старті
aiogram_thread = threading.Thread(target=lambda: asyncio.run(run_aiogram()), daemon=True)
aiogram_thread.start()

# Експортуємо Flask-додаток для gunicorn
if __name__ == "__main__":
    # Цей блок не викличеться на Railway, бо gunicorn запустить app напряму
    logger.info("Запуск Flask через gunicorn має бути виконаний командою Railway")