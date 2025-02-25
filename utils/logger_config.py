import logging
import os
from dotenv import load_dotenv

load_dotenv()

def get_database():
    from database import Database
    return Database()

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

def update_log_settings():
    db = get_database()
    debug = db.settings.get_setting("DEBUG", "0") == "1"
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    interface_info = db.settings.get_setting("INTERFACE_INFO", "0") == "1"
    api_errors = db.settings.get_setting("API_ERRORS", "0") == "1"
    transaction_info = db.settings.get_setting("TRANSACTION_INFO", "0") == "1"
    
    if interface_info:
        logger.info("Интерфейсная информация включена")
    if api_errors:
        logger.info("Логи ошибок API включены")
    if transaction_info:
        logger.info("Логи транзакций включены")
    logger.info(f"Логи обновлены. Режим отладки: {'включен' if debug else 'выключен'}")

# Функція для перевірки, чи потрібно логувати на основі налаштувань
def should_log(log_type):
    db = get_database()
    if log_type == "interface":
        return db.settings.get_setting("INTERFACE_INFO", "0") == "1"
    elif log_type == "api_errors":
        return db.settings.get_setting("API_ERRORS", "0") == "1"
    elif log_type == "transaction":
        return db.settings.get_setting("TRANSACTION_INFO", "0") == "1"
    elif log_type == "debug":
        return db.settings.get_setting("DEBUG", "0") == "1"
    return False