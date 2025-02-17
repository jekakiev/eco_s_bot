
from aiogram import Bot

BOT_TOKEN = "YOUR_BOT_TOKEN"
bot = Bot(token=BOT_TOKEN)

async def send_message(chat_id, thread_id, text):
    await bot.send_message(chat_id, text, message_thread_id=thread_id)
