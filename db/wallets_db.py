# /db/wallets_db.py
from mysql.connector import Error
from utils.logger_config import logger, should_log

class WalletsDB:
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection
        self.create_table()

    def create_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    address VARCHAR(42) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    tokens JSON DEFAULT NULL
                )
            """)
            if should_log("db"):  # Обновлено на "db" вместо "transaction"
                logger.info("Таблица wallets создана или проверена.")
        except Error as e:
            if should_log("db"):  # Обновлено на "db" вместо "api_errors"
                logger.error(f"Ошибка создания таблицы wallets: {str(e)}", exc_info=True)
            raise

    def get_all_wallets(self):
        try:
            if not self.connection.is_connected():
                if should_log("db"):
                    logger.debug("Подключение к базе разорвано, требуется переподключение")
                raise Error("Нет активного подключения к базе данных")
            if not self.cursor:
                if should_log("db"):
                    logger.debug("Курсор не инициализирован")
                raise Error("Курсор не инициализирован")
            self.cursor.execute("SELECT id, address, TRIM(name), TRIM(tokens) FROM wallets")
            results = self.cursor.fetchall()
            if should_log("debug"):
                logger.debug(f"Получены все кошельки (очищенные): {results}")
            # Проверка кодировки данных
            for result in results:
                try:
                    result[1].encode('utf-8')  # address
                    result[2].encode('utf-8')  # name
                    if result[3]:  # tokens, если существует
                        result[3].encode('utf-8')
                except UnicodeEncodeError as e:
                    if should_log("debug"):
                        logger.debug(f"Ошибка кодировки для кошелька ID={result[0]}: {str(e)}")
                    return []  # Возвращаем пустой список, если данные некорректны
            return results
        except Error as e:
            if should_log("db"):  # Обновлено на "db" вместо "api_errors"
                logger.error(f"Ошибка получения кошельков: {str(e)}", exc_info=True)
            return []

    def get_wallet_by_id(self, wallet_id):
        try:
            if should_log("debug"):
                logger.debug(f"Попытка получить кошелек с ID: {wallet_id}")
            if not self.connection.is_connected():
                if should_log("db"):
                    logger.debug(f"Подключение к базе разорвано для ID {wallet_id}, требуется переподключение")
                raise Error("Нет активного подключения к базе данных")
            if not self.cursor:
                if should_log("db"):
                    logger.debug(f"Курсор не инициализирован для ID {wallet_id}")
                raise Error("Курсор не инициализирован")
            self.cursor.execute("SELECT id, address, TRIM(name), TRIM(tokens) FROM wallets WHERE id = %s", (wallet_id,))
            result = self.cursor.fetchone()
            if should_log("debug"):
                logger.debug(f"Результат запроса для ID {wallet_id} (очищенные): {result}")
            if result is None:
                if should_log("debug"):
                    logger.debug(f"Кошелек с ID {wallet_id} не найден, проверка всех записей: {self.get_all_wallets()}")
                return None
            if not all(result) or not result[1] or not result[2]:  # Проверяем, что address и name не пустые
                if should_log("debug"):
                    logger.debug(f"Некорректные данные для кошелька с ID {wallet_id}: {result}")
                return None
            # Проверка кодировки данных
            try:
                result[1].encode('utf-8')  # address
                result[2].encode('utf-8')  # name
                if result[3]:  # tokens, если существует
                    result[3].encode('utf-8')
            except UnicodeEncodeError as e:
                if should_log("debug"):
                    logger.debug(f"Ошибка кодировки для кошелька ID={wallet_id}: {str(e)}")
                return None
            if should_log("debug"):
                logger.debug(f"Кошелек найден: ID={result[0]}, Адрес={result[1]}, Имя={result[2]}, Токены={result[3]}")
            return result
        except Error as e:
            if should_log("db"):  # Обновлено на "db" вместо "api_errors"
                logger.error(f"Ошибка получения кошелька по ID: {str(e)}", exc_info=True)
            return None

    def get_wallet_by_address(self, address):
        try:
            if not self.connection.is_connected():
                if should_log("db"):
                    logger.debug(f"Подключение к базе разорвано для адреса {address}, требуется переподключение")
                raise Error("Нет активного подключения к базе данных")
            if not self.cursor:
                if should_log("db"):
                    logger.debug(f"Курсор не инициализирован для адреса {address}")
                raise Error("Курсор не инициализирован")
            self.cursor.execute("SELECT id, address, TRIM(name), TRIM(tokens) FROM wallets WHERE address = %s", (address,))
            result = self.cursor.fetchone()
            if should_log("debug"):
                logger.debug(f"Результат поиска кошелька по адресу {address} (очищенные): {result}")
            if result:
                try:
                    result[1].encode('utf-8')  # address
                    result[2].encode('utf-8')  # name
                    if result[3]:  # tokens, если существует
                        result[3].encode('utf-8')
                except UnicodeEncodeError as e:
                    if should_log("debug"):
                        logger.debug(f"Ошибка кодировки для кошелька с адресом {address}: {str(e)}")
                    return None
            return result
        except Error as e:
            if should_log("db"):  # Обновлено на "db" вместо "api_errors"
                logger.error(f"Ошибка получения кошелька по адресу: {str(e)}", exc_info=True)
            return None

    def add_wallet(self, address, name, tokens=None):
        try:
            name_cleaned = name.strip() if name else name
            tokens_cleaned = tokens.strip() if tokens else None
            try:
                name_cleaned.encode('utf-8')
                if tokens_cleaned:
                    tokens_cleaned.encode('utf-8')
            except UnicodeEncodeError as e:
                if should_log("debug"):
                    logger.debug(f"Ошибка кодировки при добавлении кошелька: name={name_cleaned}, tokens={tokens_cleaned}, ошибка={str(e)}")
                raise ValueError("Некорректная кодировка данных")
            self.cursor.execute(
                "INSERT INTO wallets (address, name, tokens) VALUES (%s, %s, %s)",
                (address, name_cleaned, tokens_cleaned)
            )
            self.connection.commit()
            if should_log("db"):  # Обновлено на "db" вместо "transaction"
                logger.info(f"Кошелек добавлен: {name_cleaned} ({address})")
        except Error as e:
            if should_log("db"):  # Обновлено на "db" вместо "api_errors"
                logger.error(f"Ошибка добавления кошелька: {str(e)}", exc_info=True)
            self.connection.rollback()

    def update_wallet_tokens(self, wallet_id, tokens):
        try:
            tokens_cleaned = tokens.strip() if tokens else None
            try:
                if tokens_cleaned:
                    tokens_cleaned.encode('utf-8')
            except UnicodeEncodeError as e:
                if should_log("debug"):
                    logger.debug(f"Ошибка кодировки при обновлении токенов для кошелька ID {wallet_id}: tokens={tokens_cleaned}, ошибка={str(e)}")
                raise ValueError("Некорректная кодировка данных")
            self.cursor.execute(
                "UPDATE wallets SET tokens = %s WHERE id = %s",
                (tokens_cleaned, wallet_id)
            )
            self.connection.commit()
            if should_log("db"):  # Обновлено на "db" вместо "transaction"
                logger.info(f"Токены кошелька {wallet_id} обновлены")
        except Error as e:
            if should_log("db"):  # Обновлено на "db" вместо "api_errors"
                logger.error(f"Ошибка обновления токенов кошелька: {str(e)}", exc_info=True)
            self.connection.rollback()

    def rename_wallet(self, wallet_id, new_name):
        try:
            new_name_cleaned = new_name.strip()
            try:
                new_name_cleaned.encode('utf-8')
            except UnicodeEncodeError as e:
                if should_log("debug"):
                    logger.debug(f"Ошибка кодировки при переименовании кошелька ID {wallet_id}: name={new_name_cleaned}, ошибка={str(e)}")
                raise ValueError("Некорректная кодировка данных")
            self.cursor.execute(
                "UPDATE wallets SET name = %s WHERE id = %s",
                (new_name_cleaned, wallet_id)
            )
            self.connection.commit()
            if should_log("db"):  # Обновлено на "db" вместо "transaction"
                logger.info(f"Кошелек {wallet_id} переименован в {new_name_cleaned}")
        except Error as e:
            if should_log("db"):  # Обновлено на "db" вместо "api_errors"
                logger.error(f"Ошибка переименования кошелька: {str(e)}", exc_info=True)
            self.connection.rollback()

    def delete_wallet(self, wallet_id):
        try:
            self.cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id,))
            self.connection.commit()
            if should_log("db"):  # Обновлено на "db" вместо "transaction"
                logger.info(f"Кошелек {wallet_id} удален")
        except Error as e:
            if should_log("db"):  # Обновлено на "db" вместо "api_errors"
                logger.error(f"Ошибка удаления кошелька: {str(e)}", exc_info=True)
            self.connection.rollback()