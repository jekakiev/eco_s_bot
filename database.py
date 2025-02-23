import mysql.connector
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger('main_logger')

load_dotenv()

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            port=int(os.getenv("MYSQL_PORT", 3306))
        )
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.ensure_settings_exist()
        self.cursor.close()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                address VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) DEFAULT 'Невідомий',
                tokens TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tx_hash VARCHAR(255) UNIQUE NOT NULL,
                wallet_address VARCHAR(255) NOT NULL,
                token_name VARCHAR(255),
                usd_value VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracked_tokens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                token_name VARCHAR(255) NOT NULL,
                contract_address VARCHAR(255) UNIQUE NOT NULL,
                thread_id BIGINT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                setting_name VARCHAR(255) PRIMARY KEY,
                setting_value VARCHAR(255) NOT NULL
            )
        """)
        self.conn.commit()
        logger.info("Таблицы созданы или проверены.")

    def ensure_settings_exist(self):
        defaults = [
            ("CHECK_INTERVAL", "10"),
            ("SEND_LAST_TRANSACTION", "0"),
            ("API_ERRORS", "1"),
            ("TRANSACTION_INFO", "0"),
            ("INTERFACE_INFO", "0"),
            ("DEBUG", "0")
        ]
        self.cursor.execute("SELECT setting_name FROM bot_settings")
        existing_settings = {row[0] for row in self.cursor.fetchall()}
        for name, value in defaults:
            if name not in existing_settings:
                self.cursor.execute("INSERT INTO bot_settings (setting_name, setting_value) VALUES (%s, %s)", (name, value))
        self.cursor.execute("DELETE FROM bot_settings WHERE setting_name IN ('CHECK', 'LOG', 'LOG_TRANSACTIONS', 'LOG_SUCCESSFUL_TRANSACTIONS')")
        self.conn.commit()
        logger.info("Настройки инициализированы и устаревшие удалены.")

    def add_wallet(self, address, name="Невідомий", tokens=None):
        self.cursor.execute("INSERT IGNORE INTO wallets (address, name, tokens) VALUES (%s, %s, %s)", (address, name, tokens))
        self.conn.commit()
        logger.info(f"Кошелек добавлен/обновлен: {address}, {name}, {tokens}")

    def remove_wallet(self, wallet_id):
        self.cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id,))
        self.conn.commit()
        logger.info(f"Кошелек с ID {wallet_id} удалён.")

    def update_wallet_name(self, wallet_id, new_name):
        self.cursor.execute("UPDATE wallets SET name = %s WHERE id = %s", (new_name, wallet_id))
        self.conn.commit()
        logger.info(f"Имя кошелька с ID {wallet_id} обновлено на: {new_name}")

    def update_wallet_tokens(self, wallet_id, tokens):
        self.cursor.execute("UPDATE wallets SET tokens = %s WHERE id = %s", (tokens, wallet_id))
        self.conn.commit()
        logger.info(f"Токены кошелька с ID {wallet_id} обновлены на: {tokens}")

    def get_all_wallets(self):
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets")
        result = [{"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} for row in self.cursor.fetchall()]
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Получены кошельки из базы: {result}")
        return result

    def get_wallet_by_id(self, wallet_id):
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = %s", (wallet_id,))
        row = self.cursor.fetchone()
        result = {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Получен кошелек по ID {wallet_id}: {result}")
        return result

    def get_wallet_by_address(self, address):
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = %s", (address,))
        row = self.cursor.fetchone()
        result = {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Получен кошелек по адресу {address}: {result}")
        return result

    def add_transaction(self, tx_hash, wallet_address, token_name, usd_value):
        self.cursor.execute("INSERT IGNORE INTO transactions (tx_hash, wallet_address, token_name, usd_value) VALUES (%s, %s, %s, %s)",
                            (tx_hash, wallet_address, token_name, usd_value))
        self.conn.commit()
        if int(self.get_setting("TRANSACTION_INFO") or 0):
            logger.info(f"Транзакция добавлена/обновлена: {tx_hash}, {wallet_address}, {token_name}, {usd_value}")

    def is_transaction_exist(self, tx_hash):
        self.cursor.execute("SELECT 1 FROM transactions WHERE tx_hash = %s", (tx_hash,))
        result = self.cursor.fetchone() is not None
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Проверка существования транзакции {tx_hash}: {result}")
        return result

    def get_last_transaction(self):
        self.cursor.execute("SELECT tx_hash, wallet_address, token_name, usd_value, timestamp FROM transactions ORDER BY timestamp DESC LIMIT 1")
        row = self.cursor.fetchone()
        result = {
            "tx_hash": row[0],
            "wallet_address": row[1],
            "token_name": row[2],
            "usd_value": row[3],
            "timestamp": row[4]
        } if row else None
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Получена последняя транзакция: {result}")
        return result

    def add_tracked_token(self, token_name, contract_address, thread_id):
        self.cursor.execute("INSERT IGNORE INTO tracked_tokens (token_name, contract_address, thread_id) VALUES (%s, %s, %s)",
                            (token_name, contract_address, thread_id))
        self.conn.commit()
        if int(self.get_setting("INTERFACE_INFO") or 0):
            logger.info(f"Токен добавлен/обновлён: {token_name}, {contract_address}, {thread_id}")

    def update_tracked_token(self, token_id, token_name, thread_id):
        self.cursor.execute("UPDATE tracked_tokens SET token_name = %s, thread_id = %s WHERE id = %s",
                            (token_name, thread_id, token_id))
        self.conn.commit()
        if int(self.get_setting("INTERFACE_INFO") or 0):
            logger.info(f"Токен с ID {token_id} обновлён: {token_name}, {thread_id}")

    def remove_tracked_token(self, token_id):
        self.cursor.execute("DELETE FROM tracked_tokens WHERE id = %s", (token_id,))
        self.conn.commit()
        if int(self.get_setting("INTERFACE_INFO") or 0):
            logger.info(f"Токен с ID {token_id} удалён.")

    def get_all_tracked_tokens(self):
        self.cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens")
        result = [{"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} for row in self.cursor.fetchall()]
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Получены токены из базы: {result}")
        return result

    def get_tracked_token_by_id(self, token_id):
        self.cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE id = %s", (token_id,))
        row = self.cursor.fetchone()
        result = {"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} if row else None
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Получен токен по ID {token_id}: {result}")
        return result

    def get_tracked_token_by_address(self, contract_address):
        self.cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE contract_address = %s", (contract_address,))
        row = self.cursor.fetchone()
        result = {"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} if row else None
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Получен токен по адресу {contract_address}: {result}")
        return result

    def get_all_settings(self):
        self.cursor.execute("SELECT setting_name, setting_value FROM bot_settings")
        settings = {row[0]: row[1] for row in self.cursor.fetchall()}
        if int(self.get_setting("DEBUG") or 0):
            logger.debug(f"Получены настройки из базы: {settings}")
        return settings

    def get_setting(self, setting_name):
        self.cursor.execute("SELECT setting_value FROM bot_settings WHERE setting_name = %s", (setting_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_setting(self, setting_name, setting_value):
        self.cursor.execute("INSERT INTO bot_settings (setting_name, setting_value) VALUES (%s, %s) "
                            "ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)", (setting_name, setting_value))
        self.conn.commit()
        if int(self.get_setting("INTERFACE_INFO") or 0):
            logger.info(f"Настройка {setting_name} обновлена на: {setting_value}")

    def close(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()