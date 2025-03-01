# /config/bot_instance.py
from aiogram import Bot
from config.settings import BOT_TOKEN
from utils.logger_config import logger, should_log

if should_log("interface"):
    logger.info("Создание экземпляра бота")
bot = Bot(token=BOT_TOKEN)
if should_log("interface"):
    logger.info("Экземпляр бота успешно создан")

async def send_message(chat_id, thread_id, text, parse_mode="Markdown"):
    await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=text, parse_mode=parse_mode, disable_web_page_preview=True)