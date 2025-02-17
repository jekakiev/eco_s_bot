

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
import asyncio
import sqlite3

from database import add_thread

BOT_TOKEN = "YOUR_BOT_TOKEN"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["add_thread"])
async def add_thread_command(message: Message):
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.reply("❌ Формат команди: /add_thread token_id thread_id")
            return
        
        token_id = args[1]
        thread_id = int(args[2])
        
        # Отримуємо назву гілки
        chat = await bot.get_chat(message.chat.id)
        thread_name = None
        if hasattr(chat, "forum_topics"):  # Перевіряємо, чи є у чату гілки
            for thread in chat.forum_topics:
                if thread.message_thread_id == thread_id:
                    thread_name = thread.name
                    break
        
        if not thread_name:
            await message.reply("❌ Не вдалося отримати назву гілки.")
            return

        # Додаємо в базу
        success = add_thread(token_id, thread_id, thread_name)
        if success:
            await message.reply(f"✅ Додано гілку `{thread_name}` для токена `{token_id}`")
        else:
            await message.reply(f"⚠️ Гілка для `{token_id}` вже існує.")

    except Exception as e:
        await message.reply(f"❌ Помилка: {str(e)}")

if __name__ == "__main__":
    asyncio.run(dp.start_polling())


import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
