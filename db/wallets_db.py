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
                    tokens JSON DEFAULT NULL  -- Явно указываем DEFAULT NULL для JSON
                )
            """)
            if should_log("transaction"):
                logger.info("Таблица wallets создана или проверена.")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка создания таблицы wallets: {str(e)}", exc_info=True)
            raise

    def get_all_wallets(self):
        try:
            self.cursor.execute("SELECT id, address, name, tokens FROM wallets")
            results = self.cursor.fetchall()
            if should_log("debug"):
                logger.debug(f"Получены все кошельки: {results}")
            return results
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка получения кошельков: {str(e)}", exc_info=True)
            return []

    def get_wallet_by_id(self, wallet_id):
        try:
            if should_log("debug"):
                logger.debug(f"Попытка получить кошелек с ID: {wallet_id}")
            # Проверяем подключение к базе перед запросом
            if not self.connection or not self.connection.is_connected():
                if should_log("debug"):
                    logger.debug(f"Подключение к базе разорвано для ID {wallet_id}, пытаемся переподключиться")
                raise Error("Подключение к базе разорвано")
            if not self.cursor or self.cursor.closed:
                if should_log("debug"):
                    logger.debug(f"Курсор закрыт для ID {wallet_id}, создаём новый")
                self.cursor = self.connection.cursor()
            self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = %s", (wallet_id,))
            result = self.cursor.fetchone()
            if should_log("debug"):
                logger.debug(f"Результат запроса для ID {wallet_id} (rowcount: {self.cursor.rowcount}): {result}")
            if result is None:
                if should_log("debug"):
                    logger.debug(f"Кошелек с ID {wallet_id} не найден, проверка всех записей: {self.get_all_wallets()}")
                return None
            # Проверка на корректность данных
            if not all(result) or not result[1] or not result[2]:  # Проверяем, что address и name не пустые
                if should_log("debug"):
                    logger.debug(f"Некорректные данные для кошелька с ID {wallet_id}: {result}")
                return None
            if should_log("debug"):
                logger.debug(f"Кошелек найден: ID={result[0]}, Адрес={result[1]}, Имя={result[2]}, Токены={result[3]}")
            return result  # Повертаємо None, якщо гаманець не знайдено или данные некорректны
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка получения кошелька по ID: {str(e)}", exc_info=True)
            return None

    def get_wallet_by_address(self, address):
        try:
            self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = %s", (address,))
            result = self.cursor.fetchone()
            if should_log("debug"):
                logger.debug(f"Результат поиска кошелька по адресу {address}: {result}")
            return result
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка получения кошелька по адресу: {str(e)}", exc_info=True)
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
                logger.error(f"Ошибка добавления кошелька: {str(e)}", exc_info=True)
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
                logger.error(f"Ошибка обновления токенов кошелька: {str(e)}", exc_info=True)
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
                logger.error(f"Ошибка переименования кошелька: {str(e)}", exc_info=True)
            self.connection.rollback()

    def delete_wallet(self, wallet_id):
        try:
            self.cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id,))
            self.connection.commit()
            if should_log("transaction"):
                logger.info(f"Кошелек {wallet_id} удален")
        except Error as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка удаления кошелька: {str(e)}", exc_info=True)
            self.connection.rollback()