import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Ледачий імпорт Database
def get_database():
    from database import Database
    return Database()

# Налаштування логера
logger = logging.getLogger("ecoS_Parcer")
logger.setLevel(logging.INFO if os.getenv("DEBUG", "0") == "0" else logging.DEBUG)

# Налаштування формату логів
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Налаштування виводу в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Налаштування файлу логів
log_file = os.getenv("LOG_FILE", "logs/bot.log")
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def update_log_settings():
    debug = os.getenv("DEBUG", "0") == "1"
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.info(f"Логи обновлены. Режим отладки: {'включен' if debug else 'выключен'}")

# Приклад використання Database для налаштувань (без прямого імпорту)
db = get_database()  # Ініціалізуємо тут, але це може бути викликано пізніше
interface_info = db.settings.get_setting("INTERFACE_INFO", "0") == "1"
api_errors = db.settings.get_setting("API_ERRORS", "0") == "1"

if interface_info:
    logger.info("Интерфейсная информация включена")
if api_errors:
    logger.info("Логи ошибок API включены")