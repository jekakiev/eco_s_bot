import logging
from settings import LOG_TRANSACTIONS, LOG_SUCCESSFUL_TRANSACTIONS

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

# Фильтр для отключения логов о транзакциях
class TransactionsFilter(logging.Filter):
    def filter(self, record):
        if not LOG_TRANSACTIONS and "get_token_transactions вернула не список" in record.getMessage():
            return False
        return True

# Фильтр для отключения логов успешных транзакций
class SuccessfulTransactionsFilter(logging.Filter):
    def filter(self, record):
        if not LOG_SUCCESSFUL_TRANSACTIONS and ("Отримано" in record.getMessage() or "Найдено соответствие" in record.getMessage() или "Сообщение отправлено" in record.getMessage()):
            return False
        return True

# Добавление фильтров к логгеру
logger.addFilter(TransactionsFilter())
logger.addFilter(SuccessfulTransactionsFilter())

# Проверка значений переменных
logger.info(f"LOG_TRANSACTIONS: {LOG_TRANSACTIONS}")
logger.info(f"LOG_SUCCESSFUL_TRANSACTIONS: {LOG_SUCCESSFUL_TRANSACTIONS}")
