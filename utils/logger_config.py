import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Налаштування логера
logger = logging.getLogger("ecoS_Parcer")
logger.setLevel(logging.INFO if os.getenv("DEBUG", "0") == "0" else logging.DEBUG)

# Налаштування формату логів
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Створення папки logs, якщо її немає
log_dir = "/app/logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Налаштування виводу в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Налаштування файлу логів
log_file = os.path.join(log_dir, "bot.log")
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def update_log_settings(db):
    debug = db.settings.get_setting("DEBUG", "0") == "1"
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    interface_info = db.settings.get_setting("INTERFACE_INFO", "0") == "1"
    api_errors = db.settings.get_setting("API_ERRORS", "0") == "1"
    transaction_info = db.settings.get_setting("TRANSACTION_INFO", "0") == "1"
    
    if interface_info and logger.isEnabledFor(logging.INFO):
        logger.info("Интерфейсная информация включена")
    if api_errors and logger.isEnabledFor(logging.INFO):
        logger.info("Логи ошибок API включены")
    if transaction_info and logger.isEnabledFor(logging.INFO):
        logger.info("Логи транзакций включены")
    if logger.isEnabledFor(logging.INFO):
        logger.info(f"Логи обновлены. Режим отладки: {'включен' if debug else 'выключен'}")

# Функція для перевірки, чи потрібно логувати на основі налаштувань
def should_log(log_type, db=None):
    if db is None:
        try:
            from app_config import db  # Імпортуємо db з app_config, якщо не передано
        except ImportError:
            return False  # Повертаємо False, якщо db недоступний (наприклад, при ініціалізації)
    if log_type == "interface":
        return db.settings.get_setting("INTERFACE_INFO", "0") == "1"
    elif log_type == "api_errors":
        return db.settings.get_setting("API_ERRORS", "0") == "1"
    elif log_type == "transaction":
        return db.settings.get_setting("TRANSACTION_INFO", "0") == "1"
    elif log_type == "debug":
        return db.settings.get_setting("DEBUG", "0") == "1"
    return False

def get_database():
    from database import Database
    return Database()