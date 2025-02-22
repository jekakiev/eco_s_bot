import sqlite3
import os
import logging

logger = logging.getLogger('main_logger')

class Database:
    def __init__(self):
        if not os.path.exists("database.db"):
            self.conn = sqlite3.connect("database.db")
            self.create_tables()
        else:
            self.conn = sqlite3.connect("database.db")
            self.ensure_default_settings()  # Убедимся, что все настройки есть

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                tokens TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracked_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_name TEXT NOT NULL,
                contract_address TEXT UNIQUE NOT NULL,
                thread_id INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE NOT NULL,
                wallet_address TEXT NOT NULL,
                token_name TEXT NOT NULL,
                usd_value TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                setting_name TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        """)
        # Добавляем дефолтные настройки
        default_settings = {
            "CHECK_INTERVAL": "60",
            "LOG_TRANSACTIONS": "1",
            "LOG_SUCCESSFUL_TRANSACTIONS": "1",
            "SEND_LAST_TRANSACTION": "0"
        }
        for setting_name, setting_value in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO bot_settings (setting_name, setting_value) VALUES (?, ?)",
                          (setting_name, setting_value))
        self.conn.commit()
        logger.info("Таблицы и дефолтные настройки созданы или проверены.")

    def ensure_default_settings(self):
        """Убедитесь, что все дефолтные настройки присутствуют в существующей базе."""
        cursor = self.conn.cursor()
        default_settings = {
            "CHECK_INTERVAL": "60",
            "LOG_TRANSACTIONS": "1",
            "LOG_SUCCESSFUL_TRANSACTIONS": "1",
            "SEND_LAST_TRANSACTION": "0"
        }
        for setting_name, setting_value in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO bot_settings (setting_name, setting_value) VALUES (?, ?)",
                          (setting_name, setting_value))
        self.conn.commit()
        logger.info("Проверины и инициализированы дефолтные настройки в существующей базе.")

    def add_wallet(self, address, name, tokens):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT OR REPLACE INTO wallets (address, name, tokens) VALUES (?, ?, ?)", (address, name, tokens))
            self.conn.commit()
            logger.info(f"Кошелек добавлен/обновлен: {address}, {name}, {tokens}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении кошелька: {str(e)}")
            self.conn.rollback()

    def get_all_wallets(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address IS NOT NULL AND address != '' AND name IS NOT NULL AND name != ''")
            wallets = cursor.fetchall()
            logger.debug(f"Получены кошельки из базы (сырые данные): {wallets}")
            # Фильтруем пустые или некорректные записи
            valid_wallets = [w for w in wallets if w[1] and w[2]]  # Убедимся, что address и name не пустые
            logger.debug(f"Получены кошельки из базы (валидированные): {valid_wallets}")
            return valid_wallets
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении кошельков: {str(e)}")
            return []

    def get_wallet_by_id(self, wallet_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = ? AND address IS NOT NULL AND address != '' AND name IS NOT NULL AND name != ''", (wallet_id,))
            wallet = cursor.fetchone()
            logger.debug(f"Получен кошелек по ID {wallet_id}: {wallet}")
            return wallet
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении кошелька по ID {wallet_id}: {str(e)}")
            return None

    def get_wallet_by_address(self, address):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = ? AND address IS NOT NULL AND address != '' AND name IS NOT NULL AND name != ''", (address,))
            wallet = cursor.fetchone()
            logger.debug(f"Получен кошелек по адресу {address}: {wallet}")
            return wallet
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении кошелька по адресу {address}: {str(e)}")
            return None

    def remove_wallet(self, wallet_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))
            self.conn.commit()
            logger.info(f"Кошелек с ID {wallet_id} удалён.")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении кошелька с ID {wallet_id}: {str(e)}")
            self.conn.rollback()

    def update_wallet_name(self, wallet_id, new_name):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE wallets SET name = ? WHERE id = ?", (new_name, wallet_id))
            self.conn.commit()
            logger.info(f"Имя кошелька с ID {wallet_id} обновлено на: {new_name}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении имени кошелька с ID {wallet_id}: {str(e)}")
            self.conn.rollback()

    def update_wallet_tokens(self, wallet_id, tokens):
        cursor = self.conn.cursor()
        try:
            cursor.execute("UPDATE wallets SET tokens = ? WHERE id = ?", (tokens, wallet_id))
            self.conn.commit()
            logger.info(f"Токены кошелька с ID {wallet_id} обновлены на: {tokens}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении токенов кошелька с ID {wallet_id}: {str(e)}")
            self.conn.rollback()

    def add_tracked_token(self, token_name, contract_address, thread_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT OR REPLACE INTO tracked_tokens (token_name, contract_address, thread_id) VALUES (?, ?, ?)",
                          (token_name, contract_address, thread_id))
            self.conn.commit()
            logger.info(f"Токен добавлен/обновлён: {token_name}, {contract_address}, {thread_id}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении токена: {str(e)}")
            self.conn.rollback()

    def get_all_tracked_tokens(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE contract_address IS NOT NULL AND contract_address != '' AND token_name IS NOT NULL AND token_name != ''")
            tokens = cursor.fetchall()
            logger.debug(f"Получены токены из базы (сырые данные): {tokens}")
            # Фильтруем пустые или некорректные записи
            valid_tokens = [t for t in tokens if t[2] and t[1]]  # Убедимся, что contract_address и token_name не пустые
            logger.debug(f"Получены токены из базы (валидированные): {valid_tokens}")
            return valid_tokens
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении токенов: {str(e)}")
            return []

    def get_tracked_token_by_id(self, token_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE id = ? AND contract_address IS NOT NULL AND contract_address != '' AND token_name IS NOT NULL AND token_name != ''", (token_id,))
            token = cursor.fetchone()
            logger.debug(f"Получен токен по ID {token_id}: {token}")
            return token
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении токена по ID {token_id}: {str(e)}")
            return None

    def remove_tracked_token(self, token_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM tracked_tokens WHERE id = ?", (token_id,))
            self.conn.commit()
            logger.info(f"Токен с ID {token_id} удалён.")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении токена с ID {token_id}: {str(e)}")
            self.conn.rollback()

    def add_transaction(self, tx_hash, wallet_address, token_name, usd_value):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT OR REPLACE INTO transactions (tx_hash, wallet_address, token_name, usd_value) VALUES (?, ?, ?, ?)",
                          (tx_hash, wallet_address, token_name, usd_value))
            self.conn.commit()
            logger.info(f"Транзакция добавлена/обновлена: {tx_hash}, {wallet_address}, {token_name}, {usd_value}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении транзакции: {str(e)}")
            self.conn.rollback()

    def is_transaction_exist(self, tx_hash):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE tx_hash = ?", (tx_hash,))
            return cursor.fetchone()[0] > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка при проверке существования транзакции {tx_hash}: {str(e)}")
            return False

    def get_last_transaction(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT tx_hash, wallet_address, token_name, usd_value, timestamp FROM transactions ORDER BY timestamp DESC LIMIT 1")
            transaction = cursor.fetchone()
            logger.debug(f"Получена последняя транзакция: {transaction}")
            return transaction
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении последней транзакции: {str(e)}")
            return None

    def get_all_settings(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT setting_name, setting_value FROM bot_settings")
            settings = {row[0]: row[1] for row in cursor.fetchall()}
            logger.debug(f"Получены настройки из базы: {settings}")
            return settings
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении настроек: {str(e)}")
            return {}

    def get_setting(self, setting_name):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT setting_value FROM bot_settings WHERE setting_name = ?", (setting_name,))
            result = cursor.fetchone()
            logger.debug(f"Получено значение настройки {setting_name}: {result[0] if result else None}")
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении настройки {setting_name}: {str(e)}")
            return None

    def update_setting(self, setting_name, setting_value):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT OR REPLACE INTO bot_settings (setting_name, setting_value) VALUES (?, ?)",
                          (setting_name, setting_value))
            self.conn.commit()
            logger.info(f"Настройка {setting_name} обновлена на: {setting_value}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении настройки {setting_name}: {str(e)}")
            self.conn.rollback()

    def close(self):
        self.conn.close()