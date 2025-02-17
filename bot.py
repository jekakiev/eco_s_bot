import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Виводимо токен у лог (тільки для перевірки, потім треба видалити)
print(f"BOT_TOKEN from env: {BOT_TOKEN}")

# Перевіряємо, чи токен отриманий
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing or not set!")

from aiogram import Bot, Dispatcher, types
import asyncio

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("✅ Бот запущено!")

# Додаємо ще якісь хендлери (якщо були раніше)
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.reply("❓ Це бот для відстеження транзакцій.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
