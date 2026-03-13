from __future__ import annotations

from flask import Flask

from .db import init_db
from .routes import bp


def create_app() -> Flask:
    app = Flask(__name__)
    init_db()
    app.register_blueprint(bp)
    return app
