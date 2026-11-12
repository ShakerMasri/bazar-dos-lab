
from flask import Flask, jsonify, request
import sqlite3
from database import DB_PATH, init_db

app = Flask(__name__)

init_db()


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


@app.patch("/update/<int:item_number>")
def update_stock(item_number):
    data = request.get_json(silent=True)


    # Handle price updates
    if isinstance(data, dict) and set(data) == {"price"}:
        price = data["price"]

        if type(price) is not int or price < 0:
            return jsonify({"error": "Price must be a non-negative integer"}), 400

        connection = sqlite3.connect(DB_PATH, timeout=5)

        try:
            cursor = connection.execute(
                "UPDATE books SET price = ? WHERE id = ?",
                (price, item_number)
            )

            if cursor.rowcount == 0:
                return jsonify({"error": "Book not found"}), 404

            connection.commit()
        finally:
            connection.close()

        return jsonify({
            "message": "Price updated",
            "price": price
        })


    # Validate the request
    if not isinstance(data, dict) or set(data) != {"stock_delta"}:
        return jsonify({"error": "Provide stock_delta"}), 400

    delta = data["stock_delta"]

    if type(delta) is not int or delta == 0:
        return jsonify({"error": "stock_delta must be a nonzero integer"}), 400

    connection = sqlite3.connect(DB_PATH, timeout=5)

    try:
        # Atomically update stock without allowing negative quantity
        cursor = connection.execute(
            """UPDATE books
               SET quantity = quantity + ?
               WHERE id = ? AND quantity + ? >= 0""",
            (delta, item_number, delta)
        )

        if cursor.rowcount == 0:
            book = connection.execute(
                "SELECT id FROM books WHERE id = ?",
                (item_number,)
            ).fetchone()

            if book is None:
                return jsonify({"error": "Book not found"}), 404

            return jsonify({"error": "Insufficient stock"}), 409

        row = connection.execute(
            "SELECT quantity FROM books WHERE id = ?",
            (item_number,)
        ).fetchone()

        connection.commit()

    finally:
        connection.close()

    return jsonify({
        "message": "Stock updated",
        "quantity": row[0]
    })



if __name__ == "__main__":
    app.run(port=5001)
