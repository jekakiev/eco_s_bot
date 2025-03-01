# /utils/logger_config.py
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Налаштування логера
logger = logging.getLogger("ecoS_Parcer")
logger.setLevel(logging.INFO)  # Базовый уровень INFO, но вывод зависит от настроек

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

def update_log_settings(db=None):
    if db is None:
        try:
            from app_config import db
        except ImportError:
            logger.warning("Не удалось найти базу данных для обновления настроек логирования")
            return
    
    debug = db.settings.get_setting("DEBUG", "0") == "1"
    interface_info = db.settings.get_setting("INTERFACE_INFO", "0") == "1"
    transaction_info = db.settings.get_setting("TRANSACTION_INFO", "0") == "1"
    api_errors = db.settings.get_setting("API_ERRORS", "0") == "1"
    db_info = db.settings.get_setting("DB_INFO", "0") == "1"
    
    # Если все настройки выключены, поднимаем уровень до CRITICAL
    if not (debug or interface_info or transaction_info or api_errors or db_info):
        logger.setLevel(logging.CRITICAL)
    else:
        # Иначе уровень DEBUG при включённом DEBUG, иначе INFO
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Уведомления о включении каждой настройки
    if interface_info and logger.isEnabledFor(logging.INFO):
        logger.info("Интерфейсная информация включена")
    if transaction_info and logger.isEnabledFor(logging.INFO):
        logger.info("Логи транзакций включены")
    if api_errors and logger.isEnabledFor(logging.INFO):
        logger.info("Логи ошибок API включены")
    if db_info and logger.isEnabledFor(logging.INFO):
        logger.info("Логи базы данных включены")
    if logger.isEnabledFor(logging.INFO):
        logger.info(f"Логи обновлены. Режим отладки: {'включен' if debug else 'выключен'}")

# Функція для перевірки, чи потрібно логувати на основі налаштувань
def should_log(log_type, db=None):
    if db is None:
        try:
            from app_config import db
        except ImportError:
            return False
    if log_type == "interface":
        return db.settings.get_setting("INTERFACE_INFO", "0") == "1"
    elif log_type == "transaction":
        return db.settings.get_setting("TRANSACTION_INFO", "0") == "1"
    elif log_type == "api_errors":
        return db.settings.get_setting("API_ERRORS", "0") == "1"
    elif log_type == "debug":
        return db.settings.get_setting("DEBUG", "0") == "1"
    elif log_type == "db":
        return db.settings.get_setting("DB_INFO", "0") == "1"
    return False

def get_database():
    from db import Database
    return Database()