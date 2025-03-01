# /migrations.py
import mysql.connector
from mysql.connector import Error
from config.settings import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, MYSQL_PORT
from utils.logger_config import logger, should_log

def run_migrations():
    try:
        # Подключение к базе данных
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT,
            connection_timeout=10
        )
        cursor = connection.cursor()
        if should_log("db"):
            logger.info("Подключение к базе данных для миграций успешно")

        # Список миграций (SQL-команды)
        migrations = [
            # 1. Добавление SEND_LAST_TRANSACTION в settings
            """
            INSERT INTO settings (`key`, value) 
            VALUES ('SEND_LAST_TRANSACTION', '0') 
            ON DUPLICATE KEY UPDATE value = '0';
            """,
            # 2. Удаление таблицы bot_settings
            """
            DROP TABLE IF EXISTS bot_settings;
            """
        ]

        # Выполнение миграций
        for migration in migrations:
            try:
                cursor.execute(migration)
                connection.commit()
                if should_log("db"):
                    logger.info(f"Миграция выполнена: {migration.strip()[:50]}...")
            except Error as e:
                if should_log("db"):
                    logger.error(f"Ошибка выполнения миграции: {str(e)}")
                connection.rollback()
                raise

        # Закрытие соединения
        cursor.close()
        connection.close()
        if should_log("db"):
            logger.info("Миграции завершены, соединение закрыто")

    except Error as e:
        if should_log("db"):
            logger.error(f"Ошибка подключения к базе данных для миграций: {str(e)}")
        raise

if __name__ == "__main__":
    run_migrations()