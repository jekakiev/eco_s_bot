# /app_config.py
from db import Database
from utils.logger_config import logger

try:
    db = Database()
    logger.info("Экземпляр Database успешно создан в app_config")
except Exception as e:
    logger.error(f"Не удалось создать экземпляр Database в app_config: {str(e)}", exc_info=True)
    raise