import mysql.connector
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger('main_logger')

load_dotenv()

class Database:
    def _get_connection(self):
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            port=int(os.getenv("MYSQL_PORT", 3306))
        )

    def __init__(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        self.create_tables(cursor, conn)
        self.ensure_settings_exist(cursor, conn)
        cursor.close()
        conn.close()

    def create_tables(self, cursor, conn):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                address VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) DEFAULT 'Невідомий',
                tokens TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tx_hash VARCHAR(255) UNIQUE NOT NULL,
                wallet_address VARCHAR(255) NOT NULL,
                token_name VARCHAR(255),
                usd_value VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracked_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                token_name VARCHAR(255) NOT NULL,
                contract_address VARCHAR(255) UNIQUE NOT NULL,
                thread_id BIGINT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                setting_name VARCHAR(255) PRIMARY KEY,
                setting_value VARCHAR(255) NOT NULL
            )
        """)
        conn.commit()
        logger.info("Таблицы созданы или проверены.")

    def ensure_settings_exist(self, cursor, conn):
        defaults = [
            ("CHECK_INTERVAL", "10"),
            ("SEND_LAST_TRANSACTION", "0"),
            ("API_ERRORS", "1"),
            ("TRANSACTION_INFO", "0"),
            ("INTERFACE_INFO", "0"),
            ("DEBUG", "0")
        ]
        cursor.execute("SELECT setting_name FROM bot_settings")
        existing_settings = {row[0] for row in cursor.fetchall()}
        for name, value in defaults:
            if name not in existing_settings:
                cursor.execute("INSERT INTO bot_settings (setting_name, setting_value) VALUES (%s, %s)", (name, value))
        # Удаляем устаревшие настройки
        cursor.execute("DELETE FROM bot_settings WHERE setting_name IN ('CHECK', 'LOG', 'LOG_TRANSACTIONS', 'LOG_SUCCESSFUL_TRANSACTIONS')")
        conn.commit()
        logger.info("Настройки инициализированы и устаревшие удалены.")

    # ====== ФУНКЦІЇ ДЛЯ ГАМАНЦІВ ======
    def add_wallet(self, address, name="Невідомий", tokens=""):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT IGNORE INTO wallets (address, name, tokens) VALUES (%s, %s, %s)", (address, name, tokens))
            conn.commit()
            logger.info(f"Кошелек добавлен/обновлен: {address}, {name}, {tokens}")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при добавлении кошелька: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def remove_wallet(self, wallet_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id,))
            conn.commit()
            logger.info(f"Кошелек с ID {wallet_id} удалён.")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при удалении кошелька с ID {wallet_id}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def update_wallet_name(self, wallet_id, new_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE wallets SET name = %s WHERE id = %s", (new_name, wallet_id))
            conn.commit()
            logger.info(f"Имя кошелька с ID {wallet_id} обновлено на: {new_name}")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при обновлении имени кошелька с ID {wallet_id}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def update_wallet_tokens(self, wallet_id, tokens):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE wallets SET tokens = %s WHERE id = %s", (tokens, wallet_id))
            conn.commit()
            logger.info(f"Токены кошелька с ID {wallet_id} обновлены на: {tokens}")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при обновлении токенов кошелька с ID {wallet_id}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def get_all_wallets(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, address, name, tokens FROM wallets")
            result = [{"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} for row in cursor.fetchall()]
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получены кошельки из базы: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении кошельков: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()

    def get_wallet_by_id(self, wallet_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = %s", (wallet_id,))
            row = cursor.fetchone()
            result = {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получен кошелек по ID {wallet_id}: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении кошелька по ID {wallet_id}: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_wallet_by_address(self, address):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = %s", (address,))
            row = cursor.fetchone()
            result = {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получен кошелек по адресу {address}: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении кошелька по адресу {address}: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    # ====== ФУНКЦІЇ ДЛЯ ТРАНЗАКЦІЙ ======
    def add_transaction(self, tx_hash, wallet_address, token_name, usd_value):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT IGNORE INTO transactions (tx_hash, wallet_address, token_name, usd_value) VALUES (%s, %s, %s, %s)",
                          (tx_hash, wallet_address, token_name, usd_value))
            conn.commit()
            if int(db.get_setting("TRANSACTION_INFO", "0")):
                logger.info(f"Транзакция добавлена/обновлена: {tx_hash}, {wallet_address}, {token_name}, {usd_value}")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при добавлении транзакции: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def is_transaction_exist(self, tx_hash):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM transactions WHERE tx_hash = %s", (tx_hash,))
            result = cursor.fetchone() is not None
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Проверка существования транзакции {tx_hash}: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при проверке существования транзакции {tx_hash}: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    def get_last_transaction(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT tx_hash, wallet_address, token_name, usd_value, timestamp FROM transactions ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            result = {
                "tx_hash": row[0],
                "wallet_address": row[1],
                "token_name": row[2],
                "usd_value": row[3],
                "timestamp": row[4]
            } if row else None
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получена последняя транзакция: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении последней транзакции: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_wallet_transactions(self, wallet_address, limit=10):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT tx_hash, token_name, usd_value, timestamp FROM transactions WHERE wallet_address = %s ORDER BY timestamp DESC LIMIT %s", (wallet_address, limit))
            rows = cursor.fetchall()
            result = [{"tx_hash": row[0], "token_name": row[1], "usd_value": row[2], "timestamp": row[3]} for row in rows]
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получены транзакции для кошелька {wallet_address}: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении транзакций для кошелька {wallet_address}: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()

    # ====== ФУНКЦІЇ ДЛЯ ОТСЛЕЖИВАЕМЫХ ТОКЕНОВ ======
    def add_tracked_token(self, token_name, contract_address, thread_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT IGNORE INTO tracked_tokens (token_name, contract_address, thread_id) VALUES (%s, %s, %s)",
                          (token_name, contract_address, thread_id))
            conn.commit()
            if int(db.get_setting("INTERFACE_INFO", "0")):
                logger.info(f"Токен добавлен/обновлён: {token_name}, {contract_address}, {thread_id}")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при добавлении токена: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def update_tracked_token(self, token_id, token_name, thread_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE tracked_tokens SET token_name = %s, thread_id = %s WHERE id = %s",
                          (token_name, thread_id, token_id))
            conn.commit()
            if int(db.get_setting("INTERFACE_INFO", "0")):
                logger.info(f"Токен с ID {token_id} обновлён: {token_name}, {thread_id}")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при обновлении токена с ID {token_id}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def remove_tracked_token(self, token_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM tracked_tokens WHERE id = %s", (token_id,))
            conn.commit()
            if int(db.get_setting("INTERFACE_INFO", "0")):
                logger.info(f"Токен с ID {token_id} удалён.")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при удалении токена с ID {token_id}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def get_all_tracked_tokens(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens")
            result = [{"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} for row in cursor.fetchall()]
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получены токены из базы: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении токенов: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()

    def get_tracked_token_by_id(self, token_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE id = %s", (token_id,))
            row = cursor.fetchone()
            result = {"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} if row else None
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получен токен по ID {token_id}: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении токена по ID {token_id}: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_tracked_token_by_address(self, contract_address):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE contract_address = %s", (contract_address,))
            row = cursor.fetchone()
            result = {"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} if row else None
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получен токен по адресу {contract_address}: {result}")
            return result
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении токена по адресу {contract_address}: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    # ====== ФУНКЦІЇ ДЛЯ НАСТРОЄК ======
    def get_all_settings(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT setting_name, setting_value FROM bot_settings")
            settings = {row[0]: row[1] for row in cursor.fetchall()}
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получены настройки из базы: {settings}")
            return settings
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении настроек: {str(e)}")
            return {}
        finally:
            cursor.close()
            conn.close()

    def get_setting(self, setting_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT setting_value FROM bot_settings WHERE setting_name = %s", (setting_name,))
            result = cursor.fetchone()
            if int(db.get_setting("DEBUG", "0")):
                logger.debug(f"Получено значение настройки {setting_name}: {result[0] if result else None}")
            return result[0] if result else None
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при получении настройки {setting_name}: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()

    def update_setting(self, setting_name, setting_value):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO bot_settings (setting_name, setting_value) VALUES (%s, %s) "
                          "ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)", (setting_name, setting_value))
            conn.commit()
            if int(db.get_setting("INTERFACE_INFO", "0")):
                logger.info(f"Настройка {setting_name} обновлена на: {setting_value}")
        except mysql.connector.Error as e:
            logger.error(f"Ошибка при обновлении настройки {setting_name}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()