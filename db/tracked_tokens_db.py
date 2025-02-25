from mysql.connector import Error
from utils.logger_config import logger

class TrackedTokensDB:
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection

    def create_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracked_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    contract_address VARCHAR(42) NOT NULL UNIQUE,
                    token_name VARCHAR(255) NOT NULL,
                    thread_id VARCHAR(255),
                    decimals INT DEFAULT 18
                )
            """)
            logger.info("Таблица tracked_tokens создана или проверена.")
        except Error as e:
            logger.error(f"Ошибка создания таблицы tracked_tokens: {str(e)}")
            raise

    def get_all_tracked_tokens(self):
        try:
            self.cursor.execute("SELECT id, contract_address, token_name, thread_id, decimals FROM tracked_tokens")
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Ошибка получения отслеживаемых токенов: {str(e)}")
            return []

    def get_token_by_id(self, token_id):
        try:
            self.cursor.execute("SELECT id, contract_address, token_name, thread_id, decimals FROM tracked_tokens WHERE id = %s", (token_id,))
            return self.cursor.fetchone()
        except Error as e:
            logger.error(f"Ошибка получения токена по ID: {str(e)}")
            return None

    def add_tracked_token(self, contract_address, token_name, thread_id=None, decimals=18):
        try:
            self.cursor.execute(
                "INSERT INTO tracked_tokens (contract_address, token_name, thread_id, decimals) VALUES (%s, %s, %s, %s)",
                (contract_address, token_name, thread_id, decimals)
            )
            self.connection.commit()
            logger.info(f"Токен добавлен: {token_name} ({contract_address})")
        except Error as e:
            logger.error(f"Ошибка добавления токена: {str(e)}")
            self.connection.rollback()

    def update_token_thread(self, token_id, thread_id):
        try:
            self.cursor.execute(
                "UPDATE tracked_tokens SET thread_id = %s WHERE id = %s",
                (thread_id, token_id)
            )
            self.connection.commit()
            logger.info(f"Тред токена {token_id} обновлен на {thread_id}")
        except Error as e:
            logger.error(f"Ошибка обновления треда токена: {str(e)}")
            self.connection.rollback()

    def delete_tracked_token(self, token_id):
        try:
            self.cursor.execute("DELETE FROM tracked_tokens WHERE id = %s", (token_id,))
            self.connection.commit()
            logger.info(f"Токен {token_id} удален")
        except Error as e:
            logger.error(f"Ошибка удаления токена: {str(e)}")
            self.connection.rollback()