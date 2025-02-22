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

    def add_wallet(self, address, name, tokens):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO wallets (address, name, tokens) VALUES (?, ?, ?)", (address, name, tokens))
        self.conn.commit()

    def get_all_wallets(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, address, name, tokens FROM wallets")
        wallets = cursor.fetchall()
        logger.debug(f"Получены кошельки из базы: {wallets}")  # Добавляем логирование для отладки
        return wallets

    def get_wallet_by_id(self, wallet_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = ?", (wallet_id,))
        return cursor.fetchone()

    def get_wallet_by_address(self, address):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = ?", (address,))
        return cursor.fetchone()

    def remove_wallet(self, wallet_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))
        self.conn.commit()

    def update_wallet_name(self, wallet_id, new_name):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE wallets SET name = ? WHERE id = ?", (new_name, wallet_id))
        self.conn.commit()

    def update_wallet_tokens(self, wallet_id, tokens):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE wallets SET tokens = ? WHERE id = ?", (tokens, wallet_id))
        self.conn.commit()

    def add_tracked_token(self, token_name, contract_address, thread_id):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO tracked_tokens (token_name, contract_address, thread_id) VALUES (?, ?, ?)",
                       (token_name, contract_address, thread_id))
        self.conn.commit()

    def get_all_tracked_tokens(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens")
        tokens = cursor.fetchall()
        logger.debug(f"Получены токены из базы: {tokens}")  # Добавляем логирование для отладки
        return tokens

    def get_tracked_token_by_id(self, token_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE id = ?", (token_id,))
        return cursor.fetchone()

    def remove_tracked_token(self, token_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tracked_tokens WHERE id = ?", (token_id,))
        self.conn.commit()

    def add_transaction(self, tx_hash, wallet_address, token_name, usd_value):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO transactions (tx_hash, wallet_address, token_name, usd_value) VALUES (?, ?, ?, ?)",
                       (tx_hash, wallet_address, token_name, usd_value))
        self.conn.commit()

    def is_transaction_exist(self, tx_hash):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE tx_hash = ?", (tx_hash,))
        return cursor.fetchone()[0] > 0

    def get_last_transaction(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT tx_hash, wallet_address, token_name, usd_value, timestamp FROM transactions ORDER BY timestamp DESC LIMIT 1")
        return cursor.fetchone()

    def get_all_settings(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT setting_name, setting_value FROM bot_settings")
        settings = {row[0]: row[1] for row in cursor.fetchall()}
        return settings

    def get_setting(self, setting_name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT setting_value FROM bot_settings WHERE setting_name = ?", (setting_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def update_setting(self, setting_name, setting_value):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO bot_settings (setting_name, setting_value) VALUES (?, ?)",
                       (setting_name, setting_value))
        self.conn.commit()

    def close(self):
        self.conn.close()