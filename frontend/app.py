"""Client-facing REST gateway for Bazar.com."""
import logging
import os
from urllib.parse import quote

import requests
from flask import Flask, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

CATALOG_URL = os.getenv("CATALOG_URL", "http://127.0.0.1:5001").rstrip("/")
ORDER_URL = os.getenv("ORDER_URL", "http://127.0.0.1:5002").rstrip("/")


def forward(service_url, path, method="GET"):
    """Forward a request and preserve the backend HTTP status and JSON body."""
    try:
        response = requests.request(method, service_url + path, timeout=8)
        try:
            payload = response.json()
        except ValueError:
            app.logger.error("Non-JSON response from backend %s", service_url)
            return jsonify({"error": "Invalid backend response"}), 502
        return jsonify(payload), response.status_code
    except requests.RequestException:
        app.logger.exception("Backend unavailable for %s %s", method, path)
        return jsonify({"error": "Backend service unavailable"}), 503


@app.get("/health")
def health():
    return jsonify({"service": "frontend", "status": "ok"})


@app.get("/search/<topic>")
def search(topic):
    app.logger.info("Frontend search requested: %s", topic)
    return forward(CATALOG_URL, "/search/" + quote(topic, safe=""))


@app.get("/info/<int:item_number>")
def info(item_number):
    app.logger.info("Frontend book info requested: %s", item_number)
    return forward(CATALOG_URL, f"/info/{item_number}")


@app.post("/purchase/<int:item_number>")
def purchase(item_number):
    app.logger.info("Frontend purchase requested: %s", item_number)
    return forward(ORDER_URL, f"/purchase/{item_number}", method="POST")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
