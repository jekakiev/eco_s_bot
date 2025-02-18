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

    def add_wallet(self, address, name="Невідомий", tokens=""):
        """Додає новий гаманець у базу даних"""
        self.cursor.execute("INSERT OR IGNORE INTO wallets (address, name, tokens) VALUES (?, ?, ?)", (address, name, tokens))
        self.conn.commit()

    def remove_wallet(self, address):
        """Видаляє гаманець з бази даних"""
        self.cursor.execute("DELETE FROM wallets WHERE address = ?", (address,))
        self.conn.commit()

    def update_wallet(self, address, name=None, tokens=None):
        """Оновлює дані про гаманець"""
        if name:
            self.cursor.execute("UPDATE wallets SET name = ? WHERE address = ?", (name, address))
        if tokens is not None:
            self.cursor.execute("UPDATE wallets SET tokens = ? WHERE address = ?", (tokens, address))
        self.conn.commit()

    def get_all_wallets(self):
        """Отримує всі відстежувані гаманці"""
        self.cursor.execute("SELECT address, name, tokens FROM wallets")
        return [{"address": row[0], "name": row[1], "tokens": row[2]} for row in self.cursor.fetchall()]

    def add_transaction(self, tx_hash, wallet_address, token_name, usd_value):
        """Додає нову транзакцію в БД"""
        self.cursor.execute("INSERT OR IGNORE INTO transactions (tx_hash, wallet_address, token_name, usd_value) VALUES (?, ?, ?, ?)",
                            (tx_hash, wallet_address, token_name, usd_value))
        self.conn.commit()

    def is_transaction_exist(self, tx_hash):
        """Перевіряє, чи є така транзакція в БД"""
        self.cursor.execute("SELECT 1 FROM transactions WHERE tx_hash = ?", (tx_hash,))
        return self.cursor.fetchone() is not None
