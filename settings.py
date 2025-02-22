import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурационные параметры
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Без значения по умолчанию — ошибка, если не определено
if BOT_TOKEN is None:
    raise ValueError("Переменная BOT_TOKEN не определена в .env")

ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY")  # Без значения по умолчанию — ошибка, если не определено
if ARBISCAN_API_KEY is None:
    raise ValueError("Переменная ARBISCAN_API_KEY не определена в .env")

ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Без значения по умолчанию — ошибка, если не определено
if ADMIN_ID is None:
    raise ValueError("Переменная ADMIN_ID не определена в .env")

# Настройки
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL"))  # Без значения по умолчанию — ошибка, если не определено
if CHECK_INTERVAL is None:
    raise ValueError("Переменная CHECK_INTERVAL не определена в .env")

CHAT_ID = int(os.getenv("CHAT_ID"))  # Без значения по умолчанию — ошибка, если не определено
if CHAT_ID is None:
    raise ValueError("Переменная CHAT_ID не определена в .env")

# Настройка для включения/выключения логов о транзакциях
LOG_TRANSACTIONS = int(os.getenv("LOG_TRANSACTIONS"))  # Без значения по умолчанию — ошибка, если не определено
if LOG_TRANSACTIONS is None:
    raise ValueError("Переменная LOG_TRANSACTIONS не определена в .env")

# Настройка для включения/выключения логов успешных запросов
LOG_SUCCESSFUL_TRANSACTIONS = int(os.getenv("LOG_SUCCESSFUL_TRANSACTIONS"))  # Без значения по умолчанию — ошибка, если не определено
if LOG_SUCCESSFUL_TRANSACTIONS is None:
    raise ValueError("Переменная LOG_SUCCESSFUL_TRANSACTIONS не определена в .env")

# Проверка значений переменных
logger.info(f"LOG_TRANSACTIONS: {LOG_TRANSACTIONS}")
logger.info(f"LOG_SUCCESSFUL_TRANSACTIONS: {LOG_SUCCESSFUL_TRANSACTIONS}")