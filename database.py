import sqlite3

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Створення таблиць у базі даних"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT 'Невідомий',
                tokens TEXT DEFAULT ''
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE NOT NULL,
                wallet_address TEXT NOT NULL,
                token_name TEXT,
                usd_value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    # ====== ФУНКЦІЇ ДЛЯ ГАМАНЦІВ ======

    def add_wallet(self, address, name="Невідомий", tokens=""):
        """Додає новий гаманець у базу даних"""
        self.cursor.execute("INSERT OR IGNORE INTO wallets (address, name, tokens) VALUES (?, ?, ?)", (address, name, tokens))
        self.conn.commit()

    def remove_wallet(self, wallet_id):
        """Видаляє гаманець з бази даних"""
        self.cursor.execute("DELETE FROM wallets WHERE id = ?", (wallet_id,))
        self.conn.commit()

    def update_wallet_name(self, wallet_id, new_name):
        """Оновлює ім'я гаманця"""
        self.cursor.execute("UPDATE wallets SET name = ? WHERE id = ?", (new_name, wallet_id))
        self.conn.commit()

    def update_wallet_tokens(self, wallet_id, tokens):
        """Оновлює список токенів для відстежування"""
        self.cursor.execute("UPDATE wallets SET tokens = ? WHERE id = ?", (tokens, wallet_id))
        self.conn.commit()

    def get_all_wallets(self):
        """Отримує всі відстежувані гаманці"""
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets")
        return [{"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} for row in self.cursor.fetchall()]

    def get_wallet_by_id(self, wallet_id):
        """Отримує інформацію про конкретний гаманець"""
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = ?", (wallet_id,))
        row = self.cursor.fetchone()
        return {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None

    def get_wallet_by_address(self, address):
        """Отримує інформацію про гаманець за адресою"""
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = ?", (address,))
        row = self.cursor.fetchone()
        return {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None

    # ====== ФУНКЦІЇ ДЛЯ ТРАНЗАКЦІЙ ======

    def add_transaction(self, tx_hash, wallet_address, token_name, usd_value):
        """Додає нову транзакцію в БД"""
        self.cursor.execute("INSERT OR IGNORE INTO transactions (tx_hash, wallet_address, token_name, usd_value) VALUES (?, ?, ?, ?)",
                            (tx_hash, wallet_address, token_name, usd_value))
        self.conn.commit()

    def is_transaction_exist(self, tx_hash):
        """Перевіряє, чи є така транзакція в БД"""
        self.cursor.execute("SELECT 1 FROM transactions WHERE tx_hash = ?", (tx_hash,))
        return self.cursor.fetchone() is not None

    def get_last_transaction(self):
        """Отримує останню транзакцію"""
        self.cursor.execute("SELECT tx_hash, wallet_address, token_name, usd_value, timestamp FROM transactions ORDER BY timestamp DESC LIMIT 1")
        row = self.cursor.fetchone()
        return {
            "tx_hash": row[0],
            "wallet_address": row[1],
            "token_name": row[2],
            "usd_value": row[3],
            "timestamp": row[4]
        } if row else None

    def get_wallet_transactions(self, wallet_address, limit=10):
        """Отримує останні N транзакцій для конкретного гаманця"""
        self.cursor.execute("SELECT tx_hash, token_name, usd_value, timestamp FROM transactions WHERE wallet_address = ? ORDER BY timestamp DESC LIMIT ?", (wallet_address, limit))
        rows = self.cursor.fetchall()
        return [{"tx_hash": row[0], "token_name": row[1], "usd_value": row[2], "timestamp": row[3]} for row in rows]
