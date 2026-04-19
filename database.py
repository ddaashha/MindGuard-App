import sqlite3
import hashlib
from datetime import datetime

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

def init_db():
    conn = sqlite3.connect('mindguard_system.db')
    c = conn.cursor()
    # Таблиця користувачів
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    # Оновлена таблиця історії з user_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp TEXT,
            user_text TEXT,
            model_used TEXT,
            top_emotion TEXT,
            confidence REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()


def add_user(username, password):
    # Додай цей рядок на початку, щоб таблиця створилася, якщо її немає
    init_db()

    conn = sqlite3.connect('mindguard_system.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('mindguard_system.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username =? AND password =?', (username, make_hashes(password)))
    data = c.fetchone()
    conn.close()
    return data # Поверне (id,) або None