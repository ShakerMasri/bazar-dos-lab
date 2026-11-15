"""Persistent SQLite storage for the Order microservice."""
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("ORDER_DB_PATH", str(Path(__file__).resolve().parent / "orders.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db():
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                book_title TEXT NOT NULL,
                price INTEGER NOT NULL CHECK (price >= 0),
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
