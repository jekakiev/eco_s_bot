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
    debug = os.getenv("DEBUG", "0") == "1"
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.info(f"Логи обновлены. Режим отладки: {'включен' if debug else 'выключен'}")

# Видалив ініціалізацію db і логування interface_info/api_errors тут, щоб уникнути циклічного імпорту
# Ці логування тепер потрібно додати в інших файлах, де використовується logger і є доступ до db