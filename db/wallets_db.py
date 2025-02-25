from mysql.connector import Error
from utils.logger_config import logger, should_log

class WalletsDB:
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection

    def create_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    address VARCHAR(42) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    tokens JSON
                )
            """)
            if should_log("transaction"):
                logger.info("Таблица wallets создана или проверена.")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка создания таблицы wallets: {str(e)}")
            raise

    def get_all_wallets(self):
        try:
            self.cursor.execute("SELECT id, address, name, tokens FROM wallets")
            return self.cursor.fetchall()
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка получения кошельков: {str(e)}")
            return []

    def get_wallet_by_id(self, wallet_id):
        try:
            if should_log("debug"):
                logger.debug(f"Попытка получить кошелек с ID: {wallet_id}")
            self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = %s", (wallet_id,))
            result = self.cursor.fetchone()
            if should_log("debug"):
                logger.debug(f"Результат запроса для ID {wallet_id} (rowcount: {self.cursor.rowcount}): {result}")
            if result is None and should_log("debug"):
                logger.debug(f"Проверка всех записей в таблице wallets: {self.get_all_wallets()}")
            return result  # Повертаємо None, якщо гаманець не знайдено
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка получения кошелька по ID: {str(e)}", exc_info=True)
            return None

    def get_wallet_by_address(self, address):
        try:
            self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = %s", (address,))
            return self.cursor.fetchone()
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка получения кошелька по адресу: {str(e)}")
            return None

    def add_wallet(self, address, name, tokens=None):
        try:
            self.cursor.execute(
                "INSERT INTO wallets (address, name, tokens) VALUES (%s, %s, %s)",
                (address, name, tokens if tokens else None)
            )
            self.connection.commit()
            if should_log("transaction"):
                logger.info(f"Кошелек добавлен: {name} ({address})")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка добавления кошелька: {str(e)}")
            self.connection.rollback()

    def update_wallet_tokens(self, wallet_id, tokens):
        try:
            self.cursor.execute(
                "UPDATE wallets SET tokens = %s WHERE id = %s",
                (tokens, wallet_id)
            )
            self.connection.commit()
            if should_log("transaction"):
                logger.info(f"Токены кошелька {wallet_id} обновлены")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка обновления токенов кошелька: {str(e)}")
            self.connection.rollback()

    def rename_wallet(self, wallet_id, new_name):
        try:
            self.cursor.execute(
                "UPDATE wallets SET name = %s WHERE id = %s",
                (new_name, wallet_id)
            )
            self.connection.commit()
            if should_log("transaction"):
                logger.info(f"Кошелек {wallet_id} переименован в {new_name}")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка переименования кошелька: {str(e)}")
            self.connection.rollback()

    def delete_wallet(self, wallet_id):
        try:
            self.cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id,))
            self.connection.commit()
            if should_log("transaction"):
                logger.info(f"Кошелек {wallet_id} удален")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка удаления кошелька: {str(e)}")
            self.connection.rollback()