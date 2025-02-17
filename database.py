
import sqlite3

DB_PATH = "database.db"

def add_wallet(name, address):
    """Додає новий гаманець у базу."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO wallets (name, address) VALUES (?, ?)", (name, address))
        conn.commit()
    except sqlite3.IntegrityError:
        return False  # Гаманець уже є в базі
    finally:
        conn.close()
    return True

def remove_wallet(address):
    """Видаляє гаманець із бази."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wallets WHERE address = ?", (address,))
    conn.commit()
    conn.close()

def get_all_wallets():
    """Отримує список усіх гаманців."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, address FROM wallets")
    wallets = cursor.fetchall()
    conn.close()
    return wallets

def save_transaction(hash, wallet_address, amount, token, link):
    """Зберігає транзакцію, щоб не надсилати її повторно."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO transactions (hash, wallet_address, amount, token, link) VALUES (?, ?, ?, ?, ?)",
                       (hash, wallet_address, amount, token, link))
        conn.commit()
    except sqlite3.IntegrityError:
        return False  # Транзакція вже є в базі
    finally:
        conn.close()
    return True

def is_transaction_processed(hash):
    """Перевіряє, чи транзакція вже оброблена."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM transactions WHERE hash = ?", (hash,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


import sqlite3

DB_PATH = "database.db"

def add_thread(token, thread_id, thread_name):
    """Додає нову гілку в базу."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO threads (token, thread_id, thread_name) VALUES (?, ?, ?)", 
                       (token, thread_id, thread_name))
        conn.commit()
    except sqlite3.IntegrityError:
        return False  # Гілка вже є в базі
    finally:
        conn.close()
    return True

def get_thread_by_token(token):
    """Отримує Thread ID та назву за токеном."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT thread_id, thread_name FROM threads WHERE token = ?", (token,))
    result = cursor.fetchone()
    conn.close()
    return result  # (thread_id, thread_name) або None
