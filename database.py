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

        # Выводим значения переменных для отладки
        print(f"MYSQL_HOST: {host}")
        print(f"MYSQL_USER: {user}")
        print(f"MYSQL_PASSWORD: {password}")
        print(f"MYSQL_DATABASE: {database}")
        print(f"MYSQL_PORT: {port}")

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
                tokens TEXT DEFAULT ''
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
        self.cursor