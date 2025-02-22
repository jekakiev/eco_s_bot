import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL"))
CHAT_ID = int(os.getenv("CHAT_ID"))
LOG_TRANSACTIONS = int(os.getenv("LOG_TRANSACTIONS"))
LOG_SUCCESSFUL_TRANSACTIONS = int(os.getenv("LOG_SUCCESSFUL_TRANSACTIONS"))

if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN не определен")
if ARBISCAN_API_KEY is None:
    raise ValueError("ARBISCAN_API_KEY не определен")
if ADMIN_ID is None:
    raise ValueError("ADMIN_ID не определен")
if CHECK_INTERVAL is None:
    raise ValueError("CHECK_INTERVAL не определен")
if CHAT_ID is None:
    raise ValueError("CHAT_ID не определен")
if LOG_TRANSACTIONS is None:
    raise ValueError("LOG_TRANSACTIONS не определен")
if LOG_SUCCESSFUL_TRANSACTIONS is None:
    raise ValueError("LOG_SUCCESSFUL_TRANSACTIONS не определен")