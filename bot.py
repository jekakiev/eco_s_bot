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

dp = Dispatcher(storage=MemoryStorage())

logger.info("Регистрация обработчиков")
register_handlers(dp)
logger.info("Обработчики зарегистрированы")

# Регистрируем команду /Editw_<wallet_id> динамически
@dp.message(lambda message: message.text and message.text.startswith("/Editw_"))
async def dynamic_edit_wallet_command(message: types.Message):
    logger.info(f"Динамическая команда /Editw_ получена от {message.from_user.id}: {message.text}")
    if should_log("interface"):
        logger.info(f"Обработка динамической команды /Editw_ для пользователя {message.from_user.id}")
    await edit_wallet_command(message)

@dp.message(Command("start"))
async def start_command(message):
    logger.info(f"Команда /start получена от {message.from_user.id}")
    if should_log("interface"):
        logger.info(f"Команда /start обработана для пользователя {message.from_user.id}")
    menu = get_main_menu()
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=menu)

@dp.message(Command("get_last_transaction"))
async def get_last_transaction_command(message):
    logger.info(f"Команда /get_last_transaction получена от {message.from_user.id}")
    if should_log("interface"):
        logger.info(f"Команда /get_last_transaction обработана для пользователя {message.from_user.id}")
    await message.answer("Функция в разработке!")

@dp.message(Command("get_thread_id"))
async def get_thread_id_command(message):
    logger.info(f"Команда /get_thread_id получена от {message.from_user.id}")
    if should_log("interface"):
        logger.info(f"Команда /get_thread_id обработана для пользователя {message.from_user.id}")
    thread_id = message.message_thread_id if message.is_topic_message else "Нет треда"
    await message.answer(f"ID текущего треда: `{thread_id}`", parse_mode="Markdown")

async def main():
    logger.info("🚀 Бот запущен и ждет новые транзакции!")
    asyncio.create_task(start_transaction_monitoring(bot, CHAT_ID))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())