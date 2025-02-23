import logging
import os
from database import Database

logger = logging.getLogger('main_logger')
logger.setLevel(logging.DEBUG)

# Удаляем старые обработчики, если они есть
if logger.handlers:
    logger.handlers.clear()

# Создаем обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Формат логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(console_handler)

db = Database()

def update_log_settings():
    settings = db.get_all_settings()
    transaction_info = int(settings.get("TRANSACTION_INFO", "0"))
    interface_info = int(settings.get("INTERFACE_INFO", "0"))
    api_errors = int(settings.get("API_ERRORS", "1"))
    debug = int(settings.get("DEBUG", "0"))

    # Устанавливаем уровень логирования на основе настроек
    if debug:
        logger.setLevel(logging.DEBUG)
    elif api_errors or transaction_info or interface_info:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    logger.info("Обновлены настройки логов:")
    logger.info(f"- Логи транзакций: {'Включены' if transaction_info else 'Выключены'}")
    logger.info(f"- Логи интерфейса: {'Включены' if interface_info else 'Выключены'}")
    logger.info(f"- Логи ошибок API: {'Включены' if api_errors else 'Выключены'}")
    logger.info(f"- Отладочные логи: {'Включены' if debug else 'Выключены'}")

# Инициализируем настройки при запуске
update_log_settings()