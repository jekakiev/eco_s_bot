import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY")
DEFAULT_THREAD_ID = 60  # Перенесли из threads_config.py