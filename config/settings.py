# /config/settings.py
import os
from dotenv import load_dotenv
from utils.logger_config import logger, should_log

if should_log("debug"):
    logger.debug("Загрузка переменных окружения из .env")
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY")
DEFAULT_THREAD_ID = 60

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql.railway.internal")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "bHRedJRrWIqFmFpXAVFLYfdpqfPwNGjf")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "railway")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))

if should_log("debug"):
    logger.debug(f"Переменные окружения загружены: BOT_TOKEN={BOT_TOKEN[:4]}..., CHAT_ID={CHAT_ID}, ARBISCAN_API_KEY={ARBISCAN_API_KEY[:4]}..., MYSQL_HOST={MYSQL_HOST}")