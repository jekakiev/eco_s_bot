# /db/__init__.py
from .wallets_db import WalletsDB
from .tracked_tokens_db import TrackedTokensDB
from .settings_db import SettingsDB
from mysql.connector import connect, Error
from utils.logger_config import logger, should_log
import os

class Database:
    def __init__(self):
        try:
            if should_log("db"):
                logger.info("Попытка подключения к базе данных с параметрами:")
                logger.info(f"Host: {os.getenv('MYSQL_HOST', 'mysql.railway.internal')}")
                logger.info(f"User: {os.getenv('MYSQL_USER', 'root')}")
                logger.info(f"Password: {'*' * len(os.getenv('MYSQL_PASSWORD', 'bHRedJRrWIqFmFpXAVFLYfdpqfPwNGjf'))}")
                logger.info(f"Database: {os.getenv('MYSQL_DATABASE', 'railway')}")
                logger.info(f"Port: {os.getenv('MYSQL_PORT', '3306')}")
            self.connection = connect(
                host=os.getenv("MYSQL_HOST", "mysql.railway.internal"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "bHRedJRrWIqFmFpXAVFLYfdpqfPwNGjf"),
                database=os.getenv("MYSQL_DATABASE", "railway"),
                port=int(os.getenv("MYSQL_PORT", "3306")),
                connection_timeout=10
            )
            self.cursor = self.connection.cursor()
            if should_log("db"):
                logger.info("Успешно подключено к базе данных")
            self.wallets = WalletsDB(self.cursor, self.connection)
            self.tracked_tokens = TrackedTokensDB(self.cursor, self.connection)
            self.settings = SettingsDB(self.cursor, self.connection)
            
            # Проверка и добавление настройки DB_INFO
            self._ensure_settings_defaults()
            
            if should_log("db"):
                logger.info("Таблицы созданы или проверены.")
        except Error as e:
            if should_log("db"):
                logger.error(f"Ошибка подключения к базе данных: {str(e)}", exc_info=True)
            raise

    def _ensure_settings_defaults(self):
        """Проверяет и добавляет настройки по умолчанию в таблицу settings."""
        try:
            # Проверяем наличие DB_INFO
            db_info = self.settings.get_setting("DB_INFO")
            if db_info is None:
                self.settings.set_setting("DB_INFO", "0")
                if should_log("db"):
                    logger.info("Настройка DB_INFO добавлена в таблицу settings со значением 0")
        except Error as e:
            if should_log("db"):
                logger.error(f"Ошибка при добавлении настроек по умолчанию: {str(e)}", exc_info=True)
            raise

    def reconnect(self):
        if not self.connection or not self.connection.is_connected():
            try:
                if should_log("db"):
                    logger.info("Попытка переподключения к базе данных")
                self.connection = connect(
                    host=os.getenv("MYSQL_HOST", "mysql.railway.internal"),
                    user=os.getenv("MYSQL_USER", "root"),
                    password=os.getenv("MYSQL_PASSWORD", "bHRedJRrWIqFmFpXAVFLYfdpqfPwNGjf"),
                    database=os.getenv("MYSQL_DATABASE", "railway"),
                    port=int(os.getenv("MYSQL_PORT", "3306")),
                    connection_timeout=10
                )
                self.cursor = self.connection.cursor()
                if should_log("db"):
                    logger.info("Переподключение к базе данных успешно")
            except Error as e:
                if should_log("db"):
                    logger.error(f"Ошибка при переподключении к базе данных: {str(e)}", exc_info=True)
                raise

__all__ = ['Database', 'WalletsDB', 'TrackedTokensDB', 'SettingsDB']