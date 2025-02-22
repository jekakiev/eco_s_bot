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
        global LOG_TRANSACTIONS
        if not LOG_TRANSACTIONS and any(keyword in record.getMessage() for keyword in [
            "get_token_transactions вернула не словарь",
            "Найдена транзакция",
            "Транзакция уже существует",
            "Проверка транзакций завершена"
        ]):
            return False
        return True

# Фильтр для отключения логов успешных транзакций
class SuccessfulTransactionsFilter(logging.Filter):
    def filter(self, record):
        global LOG_TRANSACTIONS, LOG_SUCCESSFUL_TRANSACTIONS
        if not LOG_SUCCESSFUL_TRANSACTIONS and any(keyword in record.getMessage() for keyword in [
            "Начинаем проверку новых транзакций",
            "Обработка кошелька началась",
            "Кошелёк '",
            "обнаружено новых транзакций",
            "сообщение отправлено в тред"
        ]):
            return False
        return True

# Функция для обновления значений логов и фильтров
def update_log_settings():
    global LOG_TRANSACTIONS, LOG_SUCCESSFUL_TRANSACTIONS
    settings = db.get_all_settings()
    LOG_TRANSACTIONS = int(settings.get("LOG_TRANSACTIONS", "0"))
    LOG_SUCCESSFUL_TRANSACTIONS = int(settings.get("LOG_SUCCESSFUL_TRANSACTIONS", "0"))
    logger.info("Обновлены настройки логов:")
    logger.info(f"- Логи транзакций: {'Включены' if LOG_TRANSACTIONS else 'Выключены'}")
    logger.info(f"- Логи успешных транзакций: {'Включены' if LOG_SUCCESSFUL_TRANSACTIONS else 'Выключены'}")

# Инициализация фильтров
logger.addFilter(TransactionsFilter())
logger.addFilter(SuccessfulTransactionsFilter())

# Вызываем обновление настроек при запуске
update_log_settings()

# Дополнительная отладка для проверки значений
logger.debug(f"Инициализированы настройки логов: LOG_TRANSACTIONS={LOG_TRANSACTIONS}, LOG_SUCCESSFUL_TRANSACTIONS={LOG_SUCCESSFUL_TRANSACTIONS}")