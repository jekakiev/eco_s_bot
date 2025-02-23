import logging
import sys
from database import Database

db = Database()

logger = logging.getLogger('main_logger')

def update_log_settings():
    settings = db.get_all_settings()
    api_errors = int(settings.get("API_ERRORS", "1"))
    transaction_info = int(settings.get("TRANSACTION_INFO", "0"))
    interface_info = int(settings.get("INTERFACE_INFO", "0"))
    debug = int(settings.get("DEBUG", "0"))

    # Устанавливаем уровень логирования
    if debug:
        logger.setLevel(logging.DEBUG)
    elif transaction_info or interface_info or api_errors:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    # Очищаем старые хендлеры
    logger.handlers.clear()
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if interface_info or transaction_info:
        logger.info("Обновлены настройки логов:")
        logger.info(f"- Логи транзакций: {'Включены' if transaction_info else 'Выключены'}")
        logger.info(f"- Логи интерфейса: {'Включены' if interface_info else 'Выключены'}")
        logger.info(f"- Логи ошибок API: {'Включены' if api_errors else 'Выключены'}")
        logger.info(f"- Отладочные логи: {'Включены' if debug else 'Выключены'}")

# Инициализация при запуске
update_log_settings()