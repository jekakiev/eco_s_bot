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
            if should_log("transaction"):
                logger.info("Успешно подключено к базе данных")
            self.wallets = WalletsDB(self.cursor, self.connection)
            self.tracked_tokens = TrackedTokensDB(self.cursor, self.connection)
            self.settings = SettingsDB(self.cursor, self.connection)
        except Error as e:
            logger.error(f"Ошибка подключения к базе данных: {str(e)}", exc_info=True)
            raise

    def reconnect(self):
        if not self.connection or not self.connection.is_connected():
            try:
                self.connection = connect(
                    host=os.getenv("MYSQL_HOST", "mysql.railway.internal"),
                    user=os.getenv("MYSQL_USER", "root"),
                    password=os.getenv("MYSQL_PASSWORD", "bHRedJRrWIqFmFpXAVFLYfdpqfPwNGjf"),
                    database=os.getenv("MYSQL_DATABASE", "railway"),
                    port=int(os.getenv("MYSQL_PORT", "3306")),
                    connection_timeout=10
                )
                self.cursor = self.connection.cursor()
                if should_log("transaction"):
                    logger.info("Переподключение к базе данных успешно")
            except Error as e:
                if should_log("api_errors"):
                    logger.error(f"Ошибка при переподключении к базе данных: {str(e)}", exc_info=True)

__all__ = ['Database', 'WalletsDB', 'TrackedTokensDB', 'SettingsDB']