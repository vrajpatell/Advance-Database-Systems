from __future__ import annotations

from flask import Blueprint, jsonify, request

from . import services

bp = Blueprint("api", __name__)


@bp.get("/")
def index():
    return jsonify(
        {
            "message": "Advance Database Systems API",
            "endpoints": [
                "/health",
                "/analytics/count-by-magnitude",
                "/analytics/range",
                "/analytics/distance",
                "/analytics/day-night",
                "/analytics/clustering",
            ],
        }
    )


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/analytics/count-by-magnitude")
def count_by_magnitude():
    payload = request.get_json(silent=True) or {}
    min_magnitude = float(payload.get("min_magnitude", 0))
    return jsonify(services.count_by_magnitude(min_magnitude))


@bp.post("/analytics/range")
def range_query():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        services.find_in_range(
            float(payload["lower_mag"]),
            float(payload["upper_mag"]),
            str(payload["start_date"]),
            str(payload["end_date"]),
        )
    )


@bp.post("/analytics/distance")
def distance_query():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        services.find_within_distance(
            float(payload["latitude"]),
            float(payload["longitude"]),
            float(payload["distance_km"]),
        )
    )


@bp.post("/analytics/day-night")
def day_night_query():
    payload = request.get_json(silent=True) or {}
    min_magnitude = float(payload.get("min_magnitude", 0))
    return jsonify(services.day_night_split(min_magnitude))


@bp.post("/analytics/clustering")
def clustering_query():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        services.clustering(
            float(payload["lat1"]),
            float(payload["lon1"]),
            float(payload["lat2"]),
            float(payload["lon2"]),
            float(payload["step"]),
        )
    )
