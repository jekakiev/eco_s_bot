import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from interface import register_handlers, get_main_menu
from config.settings import BOT_TOKEN, CHAT_ID
from utils.logger_config import logger
from transaction_manager import start_transaction_monitoring

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logger.info("Регистрация обработчиков")
register_handlers(dp)
logger.info("Обработчики зарегистрированы")

@dp.message(Command("start"))
async def start_command(message):
    logger.info(f"Команда /start получена от {message.from_user.id}")
    menu = get_main_menu()
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=menu)
    settings = db.get_all_settings()
    if int(settings.get("INTERFACE_INFO", "0")):
        logger.info(f"Команда /start обработана для пользователя {message.from_user.id}")

@dp.message(Command("get_last_transaction"))
async def get_last_transaction_command(message):
    logger.info(f"Команда /get_last_transaction получена от {message.from_user.id}")
    await message.answer("Функция в разработке!")
    settings = db.get_all_settings()
    if int(settings.get("INTERFACE_INFO", "0")):
        logger.info(f"Команда /get_last_transaction обработана для пользователя {message.from_user.id}")

@dp.message(Command("get_thread_id"))
async def get_thread_id_command(message):
    logger.info(f"Команда /get_thread_id получена от {message.from_user.id}")
    thread_id = message.message_thread_id if message.is_topic_message else "Нет треда"
    await message.answer(f"ID текущего треда: `{thread_id}`", parse_mode="Markdown")
    settings = db.get_all_settings()
    if int(settings.get("INTERFACE_INFO", "0")):
        logger.info(f"Команда /get_thread_id обработана для пользователя {message.from_user.id}")

async def main():
    logger.info("🚀 Бот запущен и ждет новые транзакции!")
    asyncio.create_task(start_transaction_monitoring(bot, CHAT_ID))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())