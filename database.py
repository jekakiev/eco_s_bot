import mysql.connector
import os
from dotenv import load_dotenv

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
        self.conn.commit()

    # ====== ФУНКЦІЇ ДЛЯ ГАМАНЦІВ ======
    def add_wallet(self, address, name="Невідомий", tokens=""):
        self.cursor.execute("INSERT IGNORE INTO wallets (address, name, tokens) VALUES (%s, %s, %s)", (address, name, tokens))
        self.conn.commit()

    def remove_wallet(self, wallet_id):
        self.cursor.execute("DELETE FROM wallets WHERE id = %s", (wallet_id,))
        self.conn.commit()

    def update_wallet_name(self, wallet_id, new_name):
        self.cursor.execute("UPDATE wallets SET name = %s WHERE id = %s", (new_name, wallet_id))
        self.conn.commit()

    def update_wallet_tokens(self, wallet_id, tokens):
        self.cursor.execute("UPDATE wallets SET tokens = %s WHERE id = %s", (tokens, wallet_id))
        self.conn.commit()

    def get_all_wallets(self):
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets")
        return [{"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} for row in self.cursor.fetchall()]

    def get_wallet_by_id(self, wallet_id):
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE id = %s", (wallet_id,))
        row = self.cursor.fetchone()
        return {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None

    def get_wallet_by_address(self, address):
        self.cursor.execute("SELECT id, address, name, tokens FROM wallets WHERE address = %s", (address,))
        row = self.cursor.fetchone()
        return {"id": row[0], "address": row[1], "name": row[2], "tokens": row[3]} if row else None

    # ====== ФУНКЦІЇ ДЛЯ ТРАНЗАКЦІЙ ======
    def add_transaction(self, tx_hash, wallet_address, token_name, usd_value):
        self.cursor.execute("INSERT IGNORE INTO transactions (tx_hash, wallet_address, token_name, usd_value) VALUES (%s, %s, %s, %s)",
                            (tx_hash, wallet_address, token_name, usd_value))
        self.conn.commit()

    def is_transaction_exist(self, tx_hash):
        self.cursor.execute("SELECT 1 FROM transactions WHERE tx_hash = %s", (tx_hash,))
        return self.cursor.fetchone() is not None

    def get_last_transaction(self):
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
        self.cursor.execute("SELECT tx_hash, token_name, usd_value, timestamp FROM transactions WHERE wallet_address = %s ORDER BY timestamp DESC LIMIT %s", (wallet_address, limit))
        rows = self.cursor.fetchall()
        return [{"tx_hash": row[0], "token_name": row[1], "usd_value": row[2], "timestamp": row[3]} for row in rows]

    # ====== ФУНКЦІЇ ДЛЯ ОТСЛЕЖИВАЕМЫХ ТОКЕНОВ ======
    def add_tracked_token(self, token_name, contract_address, thread_id):
        self.cursor.execute("INSERT IGNORE INTO tracked_tokens (token_name, contract_address, thread_id) VALUES (%s, %s, %s)",
                            (token_name, contract_address, thread_id))
        self.conn.commit()

    def update_tracked_token(self, token_id, token_name, thread_id):
        self.cursor.execute("UPDATE tracked_tokens SET token_name = %s, thread_id = %s WHERE id = %s",
                            (token_name, thread_id, token_id))
        self.conn.commit()

    def remove_tracked_token(self, token_id):
        self.cursor.execute("DELETE FROM tracked_tokens WHERE id = %s", (token_id,))
        self.conn.commit()

    def get_all_tracked_tokens(self):
        self.cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens")
        return [{"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} for row in self.cursor.fetchall()]

    def get_tracked_token_by_id(self, token_id):
        self.cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE id = %s", (token_id,))
        row = self.cursor.fetchone()
        return {"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} if row else None

    def get_tracked_token_by_address(self, contract_address):
        self.cursor.execute("SELECT id, token_name, contract_address, thread_id FROM tracked_tokens WHERE contract_address = %s", (contract_address,))
        row = self.cursor.fetchone()
        return {"id": row[0], "token_name": row[1], "contract_address": row[2], "thread_id": row[3]} if row else None