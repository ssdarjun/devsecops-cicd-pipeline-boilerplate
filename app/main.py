"""
DevSecOps CI/CD Pipeline Boilerplate
Sample Python Flask application used as the pipeline target.
"""

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "message": "DevSecOps pipeline is healthy"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

