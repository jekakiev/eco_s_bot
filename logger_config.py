# logger_config.py
import logging

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),  # Лог у файл
        logging.StreamHandler()  # Вивід у консоль
    ]
)

logger = logging.getLogger(__name__)
