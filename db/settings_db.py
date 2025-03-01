# /db/settings_db.py
from mysql.connector import Error
from utils.logger_config import logger

class SettingsDB:
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection

    def create_table(self):
        try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS settings (`key` VARCHAR(255) NOT NULL PRIMARY KEY, value VARCHAR(255))")
            # Проверка и добавление MIN_OTHER_TOKEN_VALUE, если его нет
            self.cursor.execute("SELECT `key` FROM settings WHERE `key` = 'MIN_OTHER_TOKEN_VALUE'")
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO settings (`key`, value) VALUES ('MIN_OTHER_TOKEN_VALUE', '50')")
                self.connection.commit()
                logger.info("Настройка MIN_OTHER_TOKEN_VALUE добавлена в таблицу settings с дефолтным значением 50.")
            logger.info("Таблица settings создана или проверена.")
        except Error as e:
            logger.error(f"Ошибка создания таблицы settings: {str(e)}")
            raise

    def get_setting(self, key, default=None):
        try:
            self.cursor.execute("SELECT value FROM settings WHERE `key` = %s", (key,))
            result = self.cursor.fetchone()
            return result[0] if result else default
        except Error as e:
            logger.error(f"Ошибка получения настройки {key}: {str(e)}")
            return default

    def set_setting(self, key, value):
        try:
            self.cursor.execute(
                "INSERT INTO settings (`key`, value) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE value = VALUES(value)",
                (key, value)
            )
            self.connection.commit()
            logger.info(f"Настройка {key} обновлена на {value}")
        except Error as e:
            logger.error(f"Ошибка установки настройки {key}: {str(e)}")
            self.connection.rollback()