"""Purchases books through Catalog's REST API and saves successful orders."""
import logging
import os
import sqlite3

import requests
from flask import Flask, jsonify
from database import DB_PATH, init_db

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
CATALOG_URL = os.getenv("CATALOG_URL", "http://127.0.0.1:5001").rstrip("/")
init_db()


@app.get("/health")
def health():
    return jsonify({"service": "order", "status": "ok"})


@app.post("/purchase/<int:item_number>")
def purchase(item_number):
    app.logger.info("Order purchase requested: %s", item_number)

    # An HTTP request is required by the lab: Order must not read Catalog's DB.
    try:
        response = requests.get(f"{CATALOG_URL}/info/{item_number}", timeout=5)
        if response.status_code == 404:
            return jsonify({"error": "Book not found"}), 404
        response.raise_for_status()
        book = response.json()
    except (requests.RequestException, ValueError):
        app.logger.exception("Catalog lookup failed for item %s", item_number)
        return jsonify({"error": "Catalog service unavailable"}), 503

    if not isinstance(book, dict) or not all(k in book for k in ("title", "price", "quantity")):
        app.logger.error("Malformed Catalog book object for item %s", item_number)
        return jsonify({"error": "Invalid Catalog response"}), 502
    if type(book["quantity"]) is not int or book["quantity"] < 0:
        return jsonify({"error": "Invalid Catalog response"}), 502
    if not isinstance(book["title"], str) or type(book["price"]) not in (int, float):
        return jsonify({"error": "Invalid Catalog response"}), 502

    if book["quantity"] == 0:
        app.logger.info("Purchase rejected (out of stock): %s", item_number)
        return jsonify({"error": "Book out of stock"}), 409

    # Catalog's existing PATCH endpoint performs an atomic conditional UPDATE.
    # This final stock check is authoritative even if the initial GET is stale.
    try:
        response = requests.patch(
            f"{CATALOG_URL}/update/{item_number}",
            json={"stock_delta": -1}, timeout=5,
        )
        if response.status_code == 409:
            return jsonify({"error": "Book out of stock"}), 409
        if response.status_code == 404:
            return jsonify({"error": "Book not found"}), 404
        response.raise_for_status()
        updated = response.json()
        if not isinstance(updated, dict) or type(updated.get("quantity")) is not int:
            raise ValueError("Invalid Catalog update response")
    except (requests.RequestException, ValueError):
        # The PATCH might already have committed even when the reply was lost.
        app.logger.exception("Catalog decrement failed; outcome may be uncertain")
        return jsonify({
            "error": "Purchase outcome uncertain; inspect Catalog and Order logs"
        }), 503

    # This is a separate transaction from Catalog's decrement. If it fails,
    # inventory may already be lower; the limitation is documented in the report.
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as connection:
            cursor = connection.execute(
                "INSERT INTO orders (book_id, book_title, price, status) "
                "VALUES (?, ?, ?, 'completed')",
                (item_number, book["title"], book["price"]),
            )
            order_id = cursor.lastrowid
            connection.commit()
    except sqlite3.Error:
        app.logger.exception("Order record failed after Catalog stock decrement")
        return jsonify({
            "error": "Order could not be recorded",
            "warning": "Catalog stock may already have been reduced"
        }), 500

    app.logger.info("bought book %s (order %s)", book["title"], order_id)
    return jsonify({
        "message": f"bought book {book['title']}",
        "book_id": item_number,
        "price": book["price"],
        "order_id": order_id,
        "remaining_quantity": updated["quantity"],
    }), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
