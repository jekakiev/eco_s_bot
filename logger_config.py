import logging
import sys
from database import Database

# Создаём объект базы данных для доступа к настройкам
db = Database()

# Загружаем настройки из базы
settings = db.get_all_settings()
LOG_TRANSACTIONS = int(settings.get("LOG_TRANSACTIONS", "0"))
LOG_SUCCESSFUL_TRANSACTIONS = int(settings.get("LOG_SUCCESSFUL_TRANSACTIONS", "0"))

# Настраиваем логгер
logger = logging.getLogger('main_logger')
logger.setLevel(logging.INFO if LOG_TRANSACTIONS else logging.WARNING)  # Устанавливаем INFO, если LOG_TRANSACTIONS=1, иначе WARNING
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Настраиваем вывод в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Функция для обновления настроек логов на основе базы данных
def update_log_settings():
    global LOG_TRANSACTIONS, LOG_SUCCESSFUL_TRANSACTIONS
    settings = db.get_all_settings()
    LOG_TRANSACTIONS = int(settings.get("LOG_TRANSACTIONS", "0"))
    LOG_SUCCESSFUL_TRANSACTIONS = int(settings.get("LOG_SUCCESSFUL_TRANSACTIONS", "0"))
    logger.setLevel(logging.INFO if LOG_TRANSACTIONS else logging.WARNING)
    logger.info("Обновлены настройки логов:")
    logger.info(f"- Логи транзакций: {'Включены' if LOG_TRANSACTIONS else 'Выключены'}")
    logger.info(f"- Логи успешных транзакций: {'Включены' if LOG_SUCCESSFUL_TRANSACTIONS else 'Выключены'}")
    logger.debug(f"Инициализированы настройки логов: LOG_TRANSACTIONS={LOG_TRANSACTIONS}, LOG_SUCCESSFUL_TRANSACTIONS={LOG_SUCCESSFUL_TRANSACTIONS}")