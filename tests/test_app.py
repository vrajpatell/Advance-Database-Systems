from __future__ import annotations

from app import create_app


def test_health_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


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
