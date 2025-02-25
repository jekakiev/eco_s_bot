import mysql.connector
from mysql.connector import Error
from config.settings import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT
from utils.logger_config import logger
from db.wallets_db import WalletsDB
from db.tracked_tokens_db import TrackedTokensDB
from db.settings_db import SettingsDB

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        try:
            self.connection = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                port=MYSQL_PORT
            )
            self.cursor = self.connection.cursor()
            self.create_tables()
            # Ініціалізуємо екземпляри для кожної таблиці
            self.wallets = WalletsDB(self.cursor, self.connection)
            self.tracked_tokens = TrackedTokensDB(self.cursor, self.connection)
            self.settings = SettingsDB(self.cursor, self.connection)
            logger.info("База данных подключена успешно.")
        except Error as e:
            logger.error(f"Ошибка подключения к базе данных: {str(e)}")
            raise

    def create_tables(self):
        try:
            # Створюємо таблиці через екземпляри класів
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