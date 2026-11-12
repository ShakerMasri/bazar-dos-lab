
import os
import requests
from urllib.parse import quote
from flask import Flask, jsonify

app = Flask(__name__)

CATALOG_URL = os.getenv(
    "CATALOG_URL", "http://127.0.0.1:5001"
)


@app.get("/search/<topic>")
def search(topic):
    try:
        response = requests.get(
            f"{CATALOG_URL}/search/{quote(topic, safe='')}",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({"error": "Catalog service unavailable"}), 503


@app.get("/info/<int:item_number>")
def info(item_number):
    try:
        response = requests.get(
            f"{CATALOG_URL}/info/{item_number}",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException:
        return jsonify({"error": "Catalog service unavailable"}), 503



if __name__ == "__main__":
    app.run(port=5000)
