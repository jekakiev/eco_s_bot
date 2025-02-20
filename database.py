import mysql.connector
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

class Database:
    def __init__(self):
        host = os.getenv("MYSQL_HOST")
        user = os.getenv("MYSQL_USER")
        password = os.getenv("MYSQL_PASSWORD")
        database = os.getenv("MYSQL_DATABASE")
        port = int(os.getenv("MYSQL_PORT", 3306))

        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Создание таблиц в базе данных"""
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
        self.conn.commit()

    # ====== ФУНКЦІЇ ДЛЯ ГАМАНЦІВ ======

    def add_wallet(self, address, name="Невідомий", tokens=""):
        """Добавляет новый кошелек в базу данных"""
        self.cursor.execute("INSERT IGNORE INTO wallets (address, name, tokens) VALUES (%s, %s, %s)", (address, name, tokens))
        self.conn.commit()

    def remove_wallet(self, wallet_id):
        """Удаляет кошелек из базы данных"""
        self.cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id,))
        self.conn.commit()

    def update_wallet_name(self, wallet_id, new_name):
        """Обновляет имя кошелька"""
        self.cursor.execute("UPDATE wallets SET name = %s WHERE id = %s", (new_name, wallet_id))
        self.conn.commit()

    def update_wallet_tokens(self, wallet_id, tokens):
        """Обновляет список токенов для отслеживания"""
        self.cursor.execute("UPDATE wallets SET tokens = %s WHERE id = %s", (tokens, wallet_id))
        self.conn.commit()

    def get_all_wallets(self):
        """Получает все отслеживаемые кошельки"""
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets")
        return [{"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} for row in self.cursor.fetchall()]

    def get_wallet_by_id(self, wallet_id):
        """Получает информацию о конкретном кошельке"""
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = %s", (wallet_id,))
        row = self.cursor.fetchone()
        return {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None

    def get_wallet_by_address(self, address):
        """Получает информацию о кошельке по адресу"""
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = %s", (address,))
        row = self.cursor.fetchone()
        return {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None

    # ====== ФУНКЦІЇ ДЛЯ ТРАНЗАКЦІЙ ======

    def add_transaction(self, tx_hash, wallet_address, token_name, usd_value):
        """Добавляет новую транзакцию в базу данных"""
        self.cursor.execute("INSERT IGNORE INTO transactions (tx_hash, wallet_address, token_name, usd_value) VALUES (%s, %s, %s, %s)",
                            (tx_hash, wallet_address, token_name, usd_value))
        self.conn.commit()

    def is_transaction_exist(self, tx_hash):
        """Проверяет, существует ли такая транзакция в базе данных"""
        self.cursor.execute("SELECT 1 FROM transactions WHERE tx_hash = %s", (tx_hash,))
        return self.cursor.fetchone() is not None

    def get_last_transaction(self):
        """Получает последнюю транзакцию"""
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
        """Получает последние N транзакций для конкретного кошелька"""
        self.cursor.execute("SELECT tx_hash, token_name, usd_value, timestamp FROM transactions WHERE wallet_address = %s ORDER BY timestamp DESC LIMIT %s", (wallet_address, limit))
        rows = self.cursor.fetchall()
        return [{"tx_hash": row[0], "token_name": row[1], "usd_value": row[2], "timestamp": row[3]} for row in rows]
