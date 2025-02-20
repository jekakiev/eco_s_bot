import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурационные параметры
BOT_TOKEN = os.getenv("BOT_TOKEN", "7856430360:AAF8-zyIvnMldX2n11hYyyp5VrGz--vGgps")
ARBISCAN_API_KEY = os.getenv("ARBISCAN_API_KEY", "5RT7WXVN4JQWWREGG584UXVCA3E7J5WZMW")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))

# Настройки
CHECK_INTERVAL = 2  # Проверка каждые 2 секунды
CHAT_ID = -1002458140371  # Chat ID группы

# Другие настройки...

# Настройка для включения/выключения логов о транзакциях
LOG_TRANSACTIONS = 0  # 1 - включить логирование, 0 - отключить логирование
