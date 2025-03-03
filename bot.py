# /app/bot.py
import asyncio
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
async def webhook():
    if should_log("transaction"):
        logger.info("Отримано POST-запит від Moralis Streams на /webhook")
    data = request.get_json()
    if not data:
        logger.error("Отримано порожній вебхук-запит")
        return jsonify({"status": "error", "message": "No data received"}), 400
    
    if should_log("debug"):
        logger.debug(f"Дані вебхука: {data}")
    
    # Обробка даних від Moralis (наприклад, відправка повідомлення в чат)
    try:
        tx_hash = data.get("txs", [{}])[0].get("hash", "невідомий хеш")
        message = f"Нова транзакція виявлена!\nХеш: `{tx_hash}`"
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
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

async def run_flask():
    """Запуск Flask-сервера у фоновому режимі."""
    from wsgiref.simple_server import make_server
    server = make_server('0.0.0.0', 8080, app)
    logger.info("Запуск Flask-сервера на порту 8080")
    await asyncio.to_thread(server.serve_forever)

async def main():
    if should_log("interface"):
        logger.info("🚀 Бот запущен и ждет новые транзакции!")
    
    # Запускаємо Aiogram polling і Flask паралельно
    flask_task = asyncio.create_task(run_flask())
    monitoring_task = asyncio.create_task(start_transaction_monitoring(bot, CHAT_ID))
    polling_task = dp.start_polling(bot)
    
    await asyncio.gather(flask_task, monitoring_task, polling_task)

if __name__ == "__main__":
    asyncio.run(main())