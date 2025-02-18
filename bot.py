import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command  # Оновлено для aiogram 3.x
from config import BOT_TOKEN  # Імпортуємо токен напряму

# Ініціалізуємо бота та диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обробник команди /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущено!")

# Обробник команди /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("❓ Це бот для відстеження транзакцій.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
