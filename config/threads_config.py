# /config/threads_config.py
from utils.logger_config import logger, should_log

if should_log("debug"):
    logger.debug("Загрузка конфигурации тредов из threads_config.py")

# Значения по умолчанию, если токен не отслеживается
DEFAULT_THREAD_ID = 60
DEFAULT_CONTRACT_ADDRESS = None

if should_log("debug"):
    logger.debug(f"Конфигурация тредов загружена: только дефолтные значения (DEFAULT_THREAD_ID={DEFAULT_THREAD_ID})")