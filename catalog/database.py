
import sqlite3
from pathlib import Path
import os

DB_PATH = Path(
    os.getenv("DB_PATH", str(Path(__file__).resolve().parent / "catalog.db"))
)

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                price INTEGER NOT NULL CHECK (price >= 0)
            )
        """)

        books = [
            (1, "How to get a good grade in DOS in 40 minutes a day",
             "distributed systems", 5, 40),

            (2, "RPCs for Noobs",
             "distributed systems", 5, 50),

            (3, "Xen and the Art of Surviving Undergraduate School",
             "undergraduate school", 5, 45),

            (4, "Cooking for the Impatient Undergrad",
             "undergraduate school", 5, 30)
        ]

        connection.executemany("""
            INSERT OR IGNORE INTO books
            (id, title, topic, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        """, books)

        connection.commit()
    finally:
        connection.close()

