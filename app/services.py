from __future__ import annotations

import datetime as dt
import math
from typing import Any

import numpy as np
import pandas as pd

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
    lat_delta = distance_km / 111.0
    lon_scale = max(0.1, math.cos(math.radians(latitude)))
    lon_delta = distance_km / (111.0 * lon_scale)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_date, event_time, latitude, longitude, magnitude, place
            FROM earthquakes
            WHERE latitude BETWEEN ? AND ?
              AND longitude BETWEEN ? AND ?;
            """,
            (latitude - lat_delta, latitude + lat_delta, longitude - lon_delta, longitude + lon_delta),
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

    min_lat, max_lat = sorted((lat2, lat1))
    min_lon, max_lon = sorted((lon1, lon2))

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT latitude, longitude
            FROM earthquakes
            WHERE latitude BETWEEN ? AND ?
              AND longitude BETWEEN ? AND ?;
            """,
            (min_lat, max_lat, min_lon, max_lon),
        ).fetchall()

    # Pre-bin points to grid cells so counting is O(n_points + n_cells) instead of O(n_points * n_cells).
    binned_counts: dict[tuple[float, float], int] = {}
    for row in rows:
        lat_idx = math.floor((lat1 - row["latitude"]) / step)
        lon_idx = math.floor((row["longitude"] - lon1) / step)
        cell_lat = lat1 - lat_idx * step
        cell_lon = lon1 + lon_idx * step
        if cell_lat < lat2 or cell_lat > lat1 or cell_lon < lon1 or cell_lon > lon2:
            continue
        key = (round(cell_lat, 6), round(cell_lon, 6))
        binned_counts[key] = binned_counts.get(key, 0) + 1

    cells: list[dict[str, Any]] = []
    lat_steps = int(math.floor((lat1 - lat2) / step)) + 1
    lon_steps = int(math.floor((lon2 - lon1) / step)) + 1

    for lat_i in range(lat_steps):
        current_lat = round(lat1 - lat_i * step, 6)
        for lon_i in range(lon_steps):
            current_lon = round(lon1 + lon_i * step, 6)
            cells.append(
                {
                    "lat": current_lat,
                    "lon": current_lon,
                    "count": binned_counts.get((current_lat, current_lon), 0),
                }
            )

    return {"cells": cells, "total_cells": len(cells)}


def detect_anomalies(zscore_threshold: float = 2.5) -> dict[str, Any]:
    if zscore_threshold <= 0:
        raise ValueError("zscore_threshold must be positive")

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_date, event_time, latitude, longitude, depth, magnitude, place
            FROM earthquakes
            ORDER BY event_date, event_time;
            """
        ).fetchall()

    if not rows:
        return {"count": 0, "threshold": zscore_threshold, "rows": []}

    frame = pd.DataFrame([dict(row) for row in rows])
    frame["magnitude"] = pd.to_numeric(frame["magnitude"], errors="coerce")
    frame = frame.dropna(subset=["magnitude"]).copy()
    if frame.empty:
        return {"count": 0, "threshold": zscore_threshold, "rows": []}

    frame["zscore"] = (frame["magnitude"] - frame["magnitude"].mean()) / frame["magnitude"].std(ddof=0)
    frame["zscore"] = frame["zscore"].abs()
    frame = frame[frame["zscore"] >= zscore_threshold].copy()

    anomalies: list[dict[str, Any]] = []
    for record in frame.to_dict(orient="records"):
        record["zscore"] = round(float(record["zscore"]), 3)
        anomalies.append(record)

    return {"count": len(anomalies), "threshold": zscore_threshold, "rows": anomalies}


def predictive_earthquake_model(days_ahead: int = 7) -> dict[str, Any]:
    if days_ahead <= 0:
        raise ValueError("days_ahead must be positive")

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT event_date, magnitude FROM earthquakes ORDER BY event_date;"
        ).fetchall()

    frame = pd.DataFrame([dict(row) for row in rows])
    if frame.empty:
        return {"days_ahead": days_ahead, "predictions": []}
    frame["event_date"] = pd.to_datetime(frame["event_date"], format="%m/%d/%Y", errors="coerce")
    frame = frame.dropna(subset=["event_date"])
    daily_series = frame.groupby(frame["event_date"].dt.date).size().sort_index()
    daily_counts = daily_series.to_dict()

    if len(daily_counts) < 2:
        return {"days_ahead": days_ahead, "predictions": []}

    sorted_days = sorted(daily_counts.items(), key=lambda x: x[0])
    day0 = sorted_days[0][0]
    x = np.array([(d - day0).days for d, _ in sorted_days], dtype=float).reshape(-1, 1)
    y = np.array([count for _, count in sorted_days], dtype=float)

    coeffs = np.linalg.lstsq(np.hstack([x, np.ones((len(x), 1))]), y, rcond=None)[0]
    slope, intercept = float(coeffs[0]), float(coeffs[1])

    last_day = sorted_days[-1][0]
    future_offsets = np.arange(1, days_ahead + 1, dtype=float)
    future_days = [last_day + dt.timedelta(days=int(offset)) for offset in future_offsets]
    future_x = np.array([(day - day0).days for day in future_days], dtype=float)
    future_preds = np.maximum(0.0, slope * future_x + intercept)

    predictions: list[dict[str, Any]] = [
        {
            "date": day.isoformat(),
            "predicted_earthquakes": round(float(pred), 3),
        }
        for day, pred in zip(future_days, future_preds)
    ]

    return {
        "days_ahead": days_ahead,
        "model": "NumPyLeastSquaresLinearRegression",
        "predictions": predictions,
    }


def ml_clustering(eps: float = 0.5, min_samples: int = 5) -> dict[str, Any]:
    if eps <= 0:
        raise ValueError("eps must be positive")
    if min_samples <= 0:
        raise ValueError("min_samples must be positive")

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT event_date, event_time, latitude, longitude, depth, magnitude, place FROM earthquakes;"
        ).fetchall()

    if not rows:
        return {"clusters": [], "noise_points": 0, "total_points": 0}

    coords = np.array([[row["latitude"], row["longitude"]] for row in rows], dtype=float)
    labels = _dbscan_labels(coords, eps=eps, min_samples=min_samples)

    clustered_rows: list[dict[str, Any]] = []
    for row, label in zip(rows, labels):
        item = dict(row)
        item["cluster_id"] = int(label)
        clustered_rows.append(item)

    cluster_summary: dict[int, int] = {}
    for label in labels:
        cluster_summary[int(label)] = cluster_summary.get(int(label), 0) + 1

    clusters = [
        {"cluster_id": cluster_id, "count": count}
        for cluster_id, count in sorted(cluster_summary.items(), key=lambda x: x[0])
    ]
    noise_points = cluster_summary.get(-1, 0)

    return {
        "clusters": clusters,
        "noise_points": noise_points,
        "total_points": len(rows),
        "rows": clustered_rows,
    }


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


def _dbscan_labels(coords: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    n_points = len(coords)
    labels = np.full(n_points, -99, dtype=int)
    visited = np.zeros(n_points, dtype=bool)
    cluster_id = 0

    # Avoid allocating a full O(n^2) distance matrix, which can exhaust memory
    # in production (e.g., >10k points). Compute neighborhoods on demand and cache.
    neighbors_cache: dict[int, list[int]] = {}

    def neighbors_for(i: int) -> list[int]:
        cached = neighbors_cache.get(i)
        if cached is not None:
            return cached

        delta = coords - coords[i]
        distances = np.sqrt(np.sum(delta * delta, axis=1))
        points = np.flatnonzero(distances <= eps).tolist()
        neighbors_cache[i] = points
        return points

    for i in range(n_points):
        if visited[i]:
            continue
        visited[i] = True
        point_neighbors = neighbors_for(i)
        if len(point_neighbors) < min_samples:
            labels[i] = -1
            continue

        labels[i] = cluster_id
        seeds = set(point_neighbors)
        seeds.discard(i)

        while seeds:
            j = seeds.pop()
            if not visited[j]:
                visited[j] = True
                j_neighbors = neighbors_for(j)
                if len(j_neighbors) >= min_samples:
                    seeds.update(j_neighbors)
            if labels[j] in (-99, -1):
                labels[j] = cluster_id

        cluster_id += 1

    labels[labels == -99] = -1
    return labels
