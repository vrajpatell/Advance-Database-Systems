from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("PORT", "5000"))
    database_path: Path = Path(os.getenv("DATABASE_PATH", "data/earthquakes.db"))
    source_csv: Path = Path(os.getenv("SOURCE_CSV", "all_month.csv"))


settings = Settings()
