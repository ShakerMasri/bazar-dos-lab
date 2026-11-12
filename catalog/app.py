
from flask import Flask, jsonify
import sqlite3
from database import DB_PATH

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({
        "service": "catalog",
        "status": "ok"
    })


@app.get("/search/<topic>")
def search(topic):
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.execute(
            "SELECT id, title FROM books WHERE topic = ?",
            (topic,)
        )
        rows = cursor.fetchall()
    finally:
        connection.close()

    books = [
        {"id": row[0], "title": row[1]}
        for row in rows
    ]

    return jsonify(books)


@app.get("/info/<int:item_number>")
def info(item_number):
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.execute(
            "SELECT title, quantity, price FROM books WHERE id = ?",
            (item_number,)
        )
        row = cursor.fetchone()
    finally:
        connection.close()

    if row is None:
        return jsonify({"error": "Book not found"}), 404

    return jsonify({
        "title": row[0],
        "quantity": row[1],
        "price": row[2]
    })


if __name__ == "__main__":
    app.run(port=5001)
