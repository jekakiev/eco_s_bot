from mysql.connector import Error
from utils.logger_config import logger

class TransactionsDB:
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection

    def create_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    wallet_address VARCHAR(42) NOT NULL,
                    tx_hash VARCHAR(66) NOT NULL,  -- Изменено с transaction_hash на tx_hash
                    timestamp DATETIME NOT NULL,
                    block_number BIGINT NOT NULL,
                    is_processed BOOLEAN DEFAULT FALSE,
                    amount_usd DECIMAL(20, 2) DEFAULT 0.00,
                    INDEX idx_wallet_address (wallet_address),
                    INDEX idx_timestamp (timestamp),
                    UNIQUE KEY unique_tx_hash (tx_hash)  -- Изменено с unique_transaction_hash на unique_tx_hash
                )
            """)
            logger.info("Таблица transactions создана или проверена.")
        except Error as e:
            logger.error(f"Ошибка создания таблицы transactions: {str(e)}")
            raise

    def get_latest_transactions(self, wallet_address, limit=20):
        try:
            self.cursor.execute("""
                SELECT * FROM transactions 
                WHERE wallet_address = %s 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (wallet_address, limit))
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"Ошибка получения последних транзакций: {str(e)}")
            return []

    def add_transaction(self, wallet_address, tx_hash, timestamp, block_number, amount_usd):  # Изменено с transaction_hash на tx_hash
        try:
            self.cursor.execute("""
                INSERT INTO transactions (wallet_address, tx_hash, timestamp, block_number, amount_usd)  -- Изменено с transaction_hash на tx_hash
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE is_processed = FALSE
            """, (wallet_address, tx_hash, timestamp, block_number, amount_usd))  # Изменено с transaction_hash на tx_hash
            self.connection.commit()
            logger.info(f"Транзакция добавлена: {tx_hash}")
        except Error as e:
            logger.error(f"Ошибка добавления транзакции: {str(e)}")
            self.connection.rollback()

    def update_transaction(self, tx_hash, data):  # Изменено с transaction_hash на tx_hash
        try:
            set_clause = ", ".join(f"{key} = %s" for key in data.keys())
            values = list(data.values()) + [tx_hash]  # Изменено с transaction_hash на tx_hash
            self.cursor.execute(f"UPDATE transactions SET {set_clause} WHERE tx_hash = %s", values)  # Изменено с transaction_hash на tx_hash
            self.connection.commit()
            logger.info(f"Транзакция обновлена: {tx_hash}")
        except Error as e:
            logger.error(f"Ошибка обновления транзакции: {str(e)}")
            self.connection.rollback()

    def clean_old_transactions(self, wallet_address, limit=20):
        try:
            self.cursor.execute("""
                DELETE FROM transactions 
                WHERE wallet_address = %s 
                AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM transactions 
                        WHERE wallet_address = %s 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    ) AS temp
                )
            """, (wallet_address, wallet_address, limit))
            self.connection.commit()
            logger.info(f"Устаревшие транзакции для {wallet_address} удалены.")
        except Error as e:
            logger.error(f"Ошибка очистки старых транзакций: {str(e)}")
            self.connection.rollback()