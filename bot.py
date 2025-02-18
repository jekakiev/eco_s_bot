import asyncio
from aiogram import Bot, Dispatcher, types
import config  # Імпортуємо токени та API-ключі

# Ініціалізація бота з токеном із config.py
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("✅ Бот запущено!")

@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.reply("❓ Це бот для відстеження транзакцій.")

# Тут можна додавати ще хендлери, якщо були в оригінальному коді

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
