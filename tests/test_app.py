from __future__ import annotations

from app import create_app


def test_health_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_index_lists_api_endpoints() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json["message"] == "Advance Database Systems API"
    assert "/analytics/ml-clustering" in response.json["endpoints"]


def test_count_by_magnitude_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post("/analytics/count-by-magnitude", json={"min_magnitude": 2.0})

    assert response.status_code == 200
    assert "count" in response.json
    assert "rows" in response.json


def test_range_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/analytics/range",
        json={
            "lower_mag": 1.0,
            "upper_mag": 9.0,
            "start_date": "2020-01-01",
            "end_date": "2035-01-01",
        },
    )

    assert response.status_code == 200
    assert "count" in response.json
    assert "rows" in response.json


def test_distance_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/analytics/distance",
        json={"latitude": 37.7749, "longitude": -122.4194, "distance_km": 500},
    )

    assert response.status_code == 200
    assert "count" in response.json
    assert "rows" in response.json


def test_day_night_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post("/analytics/day-night", json={"min_magnitude": 2.5})

    assert response.status_code == 200
    assert "day" in response.json
    assert "night" in response.json


def test_clustering_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/analytics/clustering",
        json={"lat1": 90, "lon1": -180, "lat2": -90, "lon2": 180, "step": 10},
    )

    assert response.status_code == 200
    assert "cells" in response.json


def test_anomaly_detection_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post("/analytics/anomaly-detection", json={"zscore_threshold": 2.5})

    assert response.status_code == 200
    assert "count" in response.json


def test_predictive_earthquake_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post("/analytics/predictive-earthquake", json={"days_ahead": 5})

    assert response.status_code == 200
    assert response.json["days_ahead"] == 5
    assert "predictions" in response.json


def test_ml_clustering_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post("/analytics/ml-clustering", json={"eps": 0.8, "min_samples": 4})

    assert response.status_code == 200
    assert "clusters" in response.json
    assert "total_points" in response.json
