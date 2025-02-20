import json
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Загрузка конфигурации из JSON файла
with open('config.json', 'r', encoding='utf-8') as file:
    config_data = json.load(file)

# Конфигурационные параметры
BOT_TOKEN = os.getenv("BOT_TOKEN", "7856430360:AAF8-zyIvnMldX2n11hYyyp5VrGz--vGgps")
ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY", "5RT7WXVN4JQWWREGG584UXVCA3E7J5WZMW")
ADMIN_ID = config_data.get("admin_id", 123456789)

# Настройки
CHECK_INTERVAL = 2  # Проверка каждые 2 секунды
CHAT_ID = -1002458140371  # Chat ID группы
