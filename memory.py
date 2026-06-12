import sqlite3
import os
from datetime import datetime
from config import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "memory.db")

class Memory:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_message TEXT,
                assistant_message TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        self.conn.commit()

    def save(self, user: str, assistant: str):
        self.conn.execute(
            "INSERT INTO conversations (timestamp, user_message, assistant_message) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), user, assistant)
        )
        self.conn.commit()

    def get_recent(self, limit: int = 6) -> list:
        cursor = self.conn.execute(
            "SELECT user_message, assistant_message FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        return [{"user": r[0], "assistant": r[1]} for r in reversed(rows)]

    def save_fact(self, key: str, value: str):
        self.conn.execute(
            "INSERT OR REPLACE INTO facts (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat())
        )
        self.conn.commit()

    def get_fact(self, key: str) -> str:
        cursor = self.conn.execute("SELECT value FROM facts WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
