from __future__ import annotations

from app import create_app
from app.config import settings

app = create_app()


if __name__ == "__main__":
    app.run(host=settings.app_host, port=settings.app_port)
