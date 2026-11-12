
from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({
        "service": "catalog",
        "status": "ok"
    })


if __name__ == "__main__":
    app.run(port=5001)
