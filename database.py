import mysql.connector
from mysql.connector import Error
import os
from utils.logger_config import logger, should_log
from db.wallets_db import WalletsDB
from db.tracked_tokens_db import TrackedTokensDB
from db.settings_db import SettingsDB
from db.transactions_db import TransactionsDB

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.wallets = None
        self.tracked_tokens = None
        self.settings = None
        self.transactions = None  # Додано ініціалізацію
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "mysql.railway.internal"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "bHRedJRrWIqFmFpXAVFLYfdpqfPwNGjf"),
                database=os.getenv("MYSQL_DATABASE", "railway"),
                port=int(os.getenv("MYSQL_PORT", "3306"))
            )
            self.cursor = self.connection.cursor()
            self.wallets = WalletsDB(self.cursor, self.connection)
            self.tracked_tokens = TrackedTokensDB(self.cursor, self.connection)
            self.settings = SettingsDB(self.cursor, self.connection)
            self.transactions = TransactionsDB(self.cursor, self.connection)  # Ініціалізація
            self.create_tables()
            if should_log("transaction"):
                logger.info("База данных подключена успешно.")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка подключения к базе данных: {str(e)}")
            raise

    def create_tables(self):
        try:
            self.wallets.create_table()
            self.tracked_tokens.create_table()
            self.settings.create_table()
            self.transactions.create_table()  # Додано виклик для створення таблиці transactions
            self.connection.commit()
            if should_log("transaction"):
                logger.info("Таблицы созданы или проверены.")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка создания таблиц: {str(e)}")
            raise

    def __del__(self):
        if hasattr(self, 'cursor') and self.cursor:
            try:
                # Перевірка, чи курсор відкритий, через спробу закрити його
                try:
                    self.cursor.close()
                except AttributeError:
                    pass  # Ігноруємо, якщо атрибут closed відсутній
            except Exception as e:
                if should_log("api_errors"):
                    logger.error(f"Ошибка при закрытии курсора: {str(e)}")
        if hasattr(self, 'connection') and self.connection and self.connection.is_connected():
            try:
                self.connection.close()
            except Exception as e:
                if should_log("api_errors"):
                    logger.error(f"Ошибка при закрытии соединения: {str(e)}")
            if should_log("transaction"):
                logger.info("База данных отключена успешно.")