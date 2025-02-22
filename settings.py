import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHAT_ID = int(os.getenv("CHAT_ID"))

if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN не определен")
if ARBISCAN_API_KEY is None:
    raise ValueError("ARBISCAN_API_KEY не определен")
if ADMIN_ID is None:
    raise ValueError("ADMIN_ID не определен")
if CHAT_ID is None:
    raise ValueError("CHAT_ID не определен")