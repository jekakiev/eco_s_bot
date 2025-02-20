import logging
from settings import LOG_TRANSACTIONS

# Настройка логгера
logger = logging.getLogger('main_logger')
logger.setLevel(logging.INFO)  # Установите уровень логирования в INFO

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

# Фильтр для отключения логов о транзакциях, если LOG_TRANSACTIONS == 0
class TransactionsFilter(logging.Filter):
    def filter(self, record):
        if LOG_TRANSACTIONS == 0 and "get_token_transactions вернула не список" in record.getMessage():
            return False
        return True

# Добавление фильтра к логгеру
logger.addFilter(TransactionsFilter())
