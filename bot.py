import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from interface import register_handlers, get_main_menu
from config.settings import BOT_TOKEN, CHAT_ID
from utils.logger_config import logger
from transaction_manager import start_transaction_monitoring

logger.info("Инициализация бота")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logger.info("Регистрация обработчиков")
register_handlers(dp)
logger.info("Обработчики зарегистрированы")

@dp.message(Command("start"))
async def start_command(message):
    logger.info(f"Команда /start получена от {message.from_user.id}")
    menu = get_main_menu()
    logger.info("Меню сгенерировано")
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=menu)
    logger.info("Ответ на /start отправлен")

@dp.message(Command("get_last_transaction"))
async def get_last_transaction_command(message):
    logger.info(f"Команда /get_last_transaction получена от {message.from_user.id}")
    await message.answer("Функция в разработке!")

@dp.message(Command("get_thread_id"))
async def get_thread_id_command(message):
    logger.info(f"Команда /get_thread_id получена от {message.from_user.id}")
    thread_id = message.message_thread_id if message.is_topic_message else "Нет треда"
    await message.answer(f"ID текущего треда: `{thread_id}`", parse_mode="Markdown")

async def main():
    logger.info("🚀 Бот запущен и ждет новые транзакции!")
    asyncio.create_task(start_transaction_monitoring(bot, CHAT_ID))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())