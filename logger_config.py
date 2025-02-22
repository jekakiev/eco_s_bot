import logging
from database import Database

db = Database()
settings = db.get_all_settings()
LOG_TRANSACTIONS = int(settings.get("LOG_TRANSACTIONS", "0"))
LOG_SUCCESSFUL_TRANSACTIONS = int(settings.get("LOG_SUCCESSFUL_TRANSACTIONS", "0"))

# Настройка логгера
logger = logging.getLogger('main_logger')
logger.setLevel(logging.INFO)

# Формат логирования
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Консольный хендлер
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Обработчик для записи логов в файл
file_handler = logging.FileHandler('bot.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Фильтр для отключения логов о транзакциях
class TransactionsFilter(logging.Filter):
    def filter(self, record):
        if not LOG_TRANSACTIONS and "get_token_transactions вернула не словарь" in record.getMessage():
            return False
        return True

# Фильтр для отключения логов успешных транзакций
class SuccessfulTransactionsFilter(logging.Filter):
    def filter(self, record):
        if not LOG_SUCCESSFUL_TRANSACTIONS and any(keyword in record.getMessage() for keyword in [
            "Отримано", "Получено", "Начинаем проверку новых транзакций", "Найдено соответствие", 
            "Сообщение отправлено", "уникальных транзакций для"
        ]):
            return False
        return True

# Добавление фильтров к логгеру
logger.addFilter(TransactionsFilter())
logger.addFilter(SuccessfulTransactionsFilter())