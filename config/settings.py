import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY")
DEFAULT_THREAD_ID = 60  # Перенесли из threads_config.py

# Додаємо змінні для MySQL як константи
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql.railway.internal")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "bHRedJRrWIqFmFpXAVFLYfdpqfPwNGjf")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "railway")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))