from __future__ import annotations

import csv
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import settings


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS earthquakes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    event_time TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    depth REAL,
    magnitude REAL,
    magnitude_type TEXT,
    place TEXT,
    event_type TEXT
);
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_eq_magnitude ON earthquakes (magnitude);",
    "CREATE INDEX IF NOT EXISTS idx_eq_date ON earthquakes (event_date);",
    "CREATE INDEX IF NOT EXISTS idx_eq_lat_lon ON earthquakes (latitude, longitude);",
]


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute(CREATE_TABLE_SQL)
        for statement in INDEX_SQL:
            conn.execute(statement)
        conn.commit()

        existing_count = conn.execute("SELECT COUNT(1) FROM earthquakes;").fetchone()[0]
        if existing_count > 0:
            return

        _load_seed_data(conn, settings.source_csv)
        conn.commit()


def _load_seed_data(conn: sqlite3.Connection, csv_path: Path) -> None:
    if not csv_path.exists():
        return

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row["date"],
                row["time"],
                _to_float(row.get("latitude")),
                _to_float(row.get("longitude")),
                _to_float(row.get("depth")),
                _to_float(row.get("mag")),
                row.get("magType"),
                row.get("place"),
                row.get("type"),
            )
            for row in reader
            if row.get("date") and row.get("time") and row.get("latitude") and row.get("longitude")
        ]

    conn.executemany(
        """
        INSERT INTO earthquakes (
            event_date, event_time, latitude, longitude, depth, magnitude,
            magnitude_type, place, event_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        rows,
    )


def _to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    assert value is not None
    return float(value)
