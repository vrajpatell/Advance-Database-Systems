from __future__ import annotations

import datetime as dt
import math
from typing import Any

import numpy as np

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

    magnitudes = np.array([float(row["magnitude"]) for row in rows], dtype=float)
    mean_mag = float(np.mean(magnitudes))
    std_mag = float(np.std(magnitudes))
    if std_mag == 0:
        return {"count": 0, "threshold": zscore_threshold, "rows": []}

    anomalies: list[dict[str, Any]] = []
    for row, mag in zip(rows, magnitudes):
        zscore = abs((float(mag) - mean_mag) / std_mag)
        if zscore >= zscore_threshold:
            record = dict(row)
            record["zscore"] = round(float(zscore), 3)
            anomalies.append(record)

    return {"count": len(anomalies), "threshold": zscore_threshold, "rows": anomalies}


def predictive_earthquake_model(days_ahead: int = 7) -> dict[str, Any]:
    if days_ahead <= 0:
        raise ValueError("days_ahead must be positive")

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT event_date, magnitude FROM earthquakes ORDER BY event_date;"
        ).fetchall()

    daily_counts: dict[dt.date, int] = {}
    for row in rows:
        date_obj = dt.datetime.strptime(row["event_date"], "%m/%d/%Y").date()
        daily_counts[date_obj] = daily_counts.get(date_obj, 0) + 1

    if len(daily_counts) < 2:
        return {"days_ahead": days_ahead, "predictions": []}

    sorted_days = sorted(daily_counts.items(), key=lambda x: x[0])
    day0 = sorted_days[0][0]
    x = np.array([(d - day0).days for d, _ in sorted_days], dtype=float).reshape(-1, 1)
    y = np.array([count for _, count in sorted_days], dtype=float)

    slope, intercept = np.polyfit(x.flatten(), y, 1)

    last_day = sorted_days[-1][0]
    predictions: list[dict[str, Any]] = []
    for offset in range(1, days_ahead + 1):
        future_day = last_day + dt.timedelta(days=offset)
        future_x = np.array([[(future_day - day0).days]], dtype=float)
        predicted_count = max(0.0, float(slope * future_x[0][0] + intercept))
        predictions.append(
            {
                "date": future_day.isoformat(),
                "predicted_earthquakes": round(predicted_count, 3),
            }
        )

    return {
        "days_ahead": days_ahead,
        "model": "NumPyLinearRegression",
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

    def region_query(i: int) -> list[int]:
        dists = np.linalg.norm(coords - coords[i], axis=1)
        return [idx for idx, d in enumerate(dists) if d <= eps]

    for i in range(n_points):
        if visited[i]:
            continue
        visited[i] = True
        neighbors = region_query(i)
        if len(neighbors) < min_samples:
            labels[i] = -1
            continue

        labels[i] = cluster_id
        seeds = set(neighbors)
        seeds.discard(i)

        while seeds:
            j = seeds.pop()
            if not visited[j]:
                visited[j] = True
                j_neighbors = region_query(j)
                if len(j_neighbors) >= min_samples:
                    seeds.update(j_neighbors)
            if labels[j] in (-99, -1):
                labels[j] = cluster_id

        cluster_id += 1

    labels[labels == -99] = -1
    return labels
