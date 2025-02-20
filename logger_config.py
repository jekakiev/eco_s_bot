import logging

# Настройка логгера
logger = logging.getLogger('main_logger')
logger.setLevel(logging.ERROR)  # Показывать только ошибки и предупреждения

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
