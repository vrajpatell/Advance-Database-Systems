from __future__ import annotations

import datetime as dt
import math
from typing import Any

from .db import get_connection


def count_by_magnitude(min_magnitude: float) -> dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_date, event_time, latitude, longitude, depth, magnitude, place
            FROM earthquakes
            WHERE magnitude > ?
            ORDER BY magnitude DESC;
            """,
            (min_magnitude,),
        ).fetchall()
    return {"count": len(rows), "rows": [dict(r) for r in rows]}


def find_in_range(
    lower_mag: float, upper_mag: float, start_date: str, end_date: str
) -> dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_date, event_time, latitude, longitude, magnitude, place
            FROM earthquakes
            WHERE magnitude BETWEEN ? AND ?
              AND event_date >= ?
              AND event_date <= ?;
            """,
            (lower_mag, upper_mag, start_date, end_date),
        ).fetchall()
    return {"count": len(rows), "rows": [dict(r) for r in rows]}


def find_within_distance(latitude: float, longitude: float, distance_km: float) -> dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT event_date, event_time, latitude, longitude, magnitude, place FROM earthquakes;"
        ).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        d = _haversine_km(latitude, longitude, row["latitude"], row["longitude"])
        if d <= distance_km:
            result = dict(row)
            result["distance_km"] = round(d, 3)
            results.append(result)

    return {"count": len(results), "rows": results}


def day_night_split(min_magnitude: float) -> dict[str, int]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT event_date, event_time, longitude FROM earthquakes WHERE magnitude > ?;",
            (min_magnitude,),
        ).fetchall()

    day, night = 0, 0
    for row in rows:
        event_dt = dt.datetime.strptime(
            f"{row['event_date']} {row['event_time']}", "%m/%d/%Y %H:%M:%S"
        )
        utc_offset = row["longitude"] * 24 / 360
        local_dt = event_dt - dt.timedelta(hours=utc_offset)
        if local_dt.hour < 8 or local_dt.hour > 20:
            night += 1
        else:
            day += 1

    return {"day": day, "night": night}


def clustering(lat1: float, lon1: float, lat2: float, lon2: float, step: float) -> dict[str, Any]:
    if step <= 0:
        raise ValueError("step must be positive")

    with get_connection() as conn:
        rows = conn.execute("SELECT latitude, longitude FROM earthquakes;").fetchall()

    cells: list[dict[str, Any]] = []
    current_lat = lat1
    while current_lat >= lat2:
        current_lon = lon1
        while current_lon <= lon2:
            next_lat = current_lat - step
            next_lon = current_lon + step
            count = sum(
                1
                for row in rows
                if next_lat <= row["latitude"] <= current_lat
                and current_lon <= row["longitude"] <= next_lon
            )
            cells.append({"lat": current_lat, "lon": current_lon, "count": count})
            current_lon += step
        current_lat -= step

    return {"cells": cells, "total_cells": len(cells)}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c
