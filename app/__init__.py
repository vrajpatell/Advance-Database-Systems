from __future__ import annotations

import logging

from flask import Flask, jsonify

from .db import init_db
from .routes import bp


def create_app() -> Flask:
    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO)
    init_db()
    app.register_blueprint(bp)

    @app.errorhandler(ValueError)
    def handle_value_error(exc: ValueError):
        app.logger.warning("Validation error: %s", exc)
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        app.logger.exception("Unhandled API error")
        return jsonify({"error": "internal server error"}), 500

    return app
