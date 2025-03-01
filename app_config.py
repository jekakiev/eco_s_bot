# /app_config.py
from db import Database
from utils.logger_config import logger, should_log

try:
    if should_log("db"):
        logger.info("Инициализация экземпляра Database в app_config")
    db = Database()
    if should_log("db"):
        logger.info("Экземпляр Database успешно создан в app_config")
except Exception as e:
    if should_log("db"):
        logger.error(f"Не удалось создать экземпляр Database в app_config: {str(e)}", exc_info=True)
    raise