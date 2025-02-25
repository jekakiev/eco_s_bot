import mysql.connector
from mysql.connector import Error
import os
from utils.logger_config import logger
from db.wallets_db import WalletsDB
from db.tracked_tokens_db import TrackedTokensDB
from db.settings_db import SettingsDB

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.wallets = None  # Ініціалізація атрибутів як None
        self.tracked_tokens = None
        self.settings = None
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "mysql.railway.internal"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "bHRedJRrWIqFmFpXAVFLYfdpqfPwNGjf"),
                database=os.getenv("MYSQL_DATABASE", "railway"),
                port=int(os.getenv("MYSQL_PORT", "3306"))
            )
            self.cursor = self.connection.cursor()
            # Ініціалізація атрибутів до створення таблиць
            self.wallets = WalletsDB(self.cursor, self.connection)
            self.tracked_tokens = TrackedTokensDB(self.cursor, self.connection)
            self.settings = SettingsDB(self.cursor, self.connection)
            self.create_tables()
            logger.info("База данных подключена успешно.")
        except Error as e:
            logger.error(f"Ошибка подключения к базе данных: {str(e)}")
            raise

    def create_tables(self):
        try:
            self.wallets.create_table()
            self.tracked_tokens.create_table()
            self.settings.create_table()
            self.connection.commit()
            logger.info("Таблицы созданы или проверены.")
        except Error as e:
            logger.error(f"Ошибка создания таблиц: {str(e)}")
            raise

    def __del__(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logger.info("База данных отключена успешно.")