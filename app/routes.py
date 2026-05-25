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
                "/analytics/anomaly-detection",
                "/analytics/predictive-earthquake",
                "/analytics/ml-clustering",
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


@bp.post("/analytics/anomaly-detection")
def anomaly_detection_query():
    payload = request.get_json(silent=True) or {}
    threshold = float(payload.get("zscore_threshold", 2.5))
    return jsonify(services.detect_anomalies(threshold))


@bp.post("/analytics/predictive-earthquake")
def predictive_earthquake_query():
    payload = request.get_json(silent=True) or {}
    days_ahead = int(payload.get("days_ahead", 7))
    return jsonify(services.predictive_earthquake_model(days_ahead))


@bp.post("/analytics/ml-clustering")
def ml_clustering_query():
    payload = request.get_json(silent=True) or {}
    eps = float(payload.get("eps", 0.5))
    min_samples = int(payload.get("min_samples", 5))
    return jsonify(services.ml_clustering(eps=eps, min_samples=min_samples))
