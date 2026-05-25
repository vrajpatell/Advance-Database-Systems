from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/earthquakes.db"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000").rstrip("/")
DEFAULT_TIMEOUT = 20


@st.cache_data(ttl=120)
def _post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json() if response.content else {}


@st.cache_data(ttl=120)
def _get(endpoint: str) -> dict[str, Any]:
    response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json() if response.content else {}


@st.cache_data
def load_local_data() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query("SELECT * FROM earthquakes", conn)
    finally:
        conn.close()


def _rows_df(payload: dict[str, Any]) -> pd.DataFrame:
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _safe_call(callable_obj):
    start = time.perf_counter()
    try:
        payload = callable_obj()
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        return payload, {"ok": True, "elapsed_ms": elapsed_ms}
    except requests.RequestException as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        response = getattr(exc, "response", None)
        status_code = response.status_code if response is not None else None
        return None, {
            "ok": False,
            "elapsed_ms": elapsed_ms,
            "status_code": status_code,
            "error": str(exc),
        }


def main() -> None:
    st.set_page_config(page_title="Earthquake Analytics Dashboard", layout="wide")
    st.title("Advance Database Systems — Analytics Dashboard")

    if not API_BASE_URL:
        st.error("Set API_BASE_URL in dashboard environment.")
        return

    st.sidebar.header("Query Controls")
    min_mag = st.sidebar.slider("Min magnitude", 0.0, 9.0, 4.5, 0.1)
    date_col1, date_col2 = st.sidebar.columns(2)
    start_date = date_col1.date_input("Start", value=pd.Timestamp("2020-01-01"))
    end_date = date_col2.date_input("End", value=pd.Timestamp("2022-12-31"))
    radius_km = st.sidebar.slider("Distance radius (km)", 50, 4000, 1000, 50)
    center_lat = st.sidebar.number_input("Center latitude", value=34.05, format="%.3f")
    center_lon = st.sidebar.number_input("Center longitude", value=-118.24, format="%.3f")
    zscore_threshold = st.sidebar.slider("Anomaly z-score threshold", 1.0, 5.0, 2.5, 0.1)
    days_ahead = st.sidebar.slider("Prediction horizon (days)", 1, 30, 7)
    eps = st.sidebar.slider("DBSCAN eps", 0.1, 5.0, 0.5, 0.1)
    min_samples = st.sidebar.slider("DBSCAN min_samples", 2, 30, 5)

    requests_map = {
        "health": lambda: _get("/health"),
        "count": lambda: _post("/analytics/count-by-magnitude", {"min_magnitude": min_mag}),
        "range": lambda: _post(
            "/analytics/range",
            {
                "lower_mag": min_mag,
                "upper_mag": 9.9,
                "start_date": pd.Timestamp(start_date).strftime("%m/%d/%Y"),
                "end_date": pd.Timestamp(end_date).strftime("%m/%d/%Y"),
            },
        ),
        "distance": lambda: _post(
            "/analytics/distance",
            {"latitude": center_lat, "longitude": center_lon, "distance_km": radius_km},
        ),
        "day_night": lambda: _post("/analytics/day-night", {"min_magnitude": min_mag}),
        "clustering": lambda: _post(
            "/analytics/clustering",
            {"lat1": 60.0, "lon1": -180.0, "lat2": -60.0, "lon2": 180.0, "step": 20.0},
        ),
        "anomaly": lambda: _post("/analytics/anomaly-detection", {"zscore_threshold": zscore_threshold}),
        "predictive": lambda: _post("/analytics/predictive-earthquake", {"days_ahead": days_ahead}),
        "ml": lambda: _post("/analytics/ml-clustering", {"eps": eps, "min_samples": min_samples}),
    }

    responses: dict[str, dict[str, Any]] = {}
    failures: dict[str, dict[str, Any]] = {}
    diagnostics: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(requests_map))) as pool:
        future_map = {name: pool.submit(_safe_call, fn) for name, fn in requests_map.items()}
        for name, fut in future_map.items():
            payload, meta = fut.result()
            diagnostics[name] = meta
            if not meta.get("ok"):
                failures[name] = meta
            else:
                responses[name] = payload or {}

    if failures:
        st.warning(f"Some API calls failed ({len(failures)}/{len(requests_map)}). Showing partial results.")

    with st.expander("Monitoring logs (lightweight)"):
        diagnostic_rows = []
        for endpoint_name in requests_map:
            info = diagnostics.get(endpoint_name, {})
            diagnostic_rows.append(
                {
                    "endpoint": endpoint_name,
                    "status": "ok" if info.get("ok") else "failed",
                    "http_status": info.get("status_code"),
                    "latency_ms": info.get("elapsed_ms"),
                    "error": info.get("error"),
                }
            )
        st.dataframe(pd.DataFrame(diagnostic_rows), use_container_width=True)

    if "health" not in responses:
        st.error(f"Could not connect to API {API_BASE_URL}.")
        local_data = load_local_data()
        if not local_data.empty:
            st.info("Local SQLite data found, but dashboard requires API for endpoint analytics.")
        return

    health = responses.get("health", {})
    count_payload = responses.get("count", {})
    range_payload = responses.get("range", {})
    distance_payload = responses.get("distance", {})
    day_night_payload = responses.get("day_night", {})
    clustering_payload = responses.get("clustering", {})
    anomaly_payload = responses.get("anomaly", {})
    pred_payload = responses.get("predictive", {})
    ml_cluster_payload = responses.get("ml", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("API Health", health.get("status", "unknown").upper())
    c2.metric("Count > Min Mag", count_payload.get("count", 0))
    c3.metric("Range Matches", range_payload.get("count", 0))
    c4.metric("Nearby Events", distance_payload.get("count", 0))

    st.subheader("Endpoint Coverage Overview")
    endpoint_counts = pd.DataFrame(
        [
            {"endpoint": "count-by-magnitude", "count": count_payload.get("count", 0)},
            {"endpoint": "range", "count": range_payload.get("count", 0)},
            {"endpoint": "distance", "count": distance_payload.get("count", 0)},
            {
                "endpoint": "anomaly-detection",
                "count": anomaly_payload.get("count", 0),
            },
            {
                "endpoint": "ml-clustering (labeled rows)",
                "count": ml_cluster_payload.get("total_points", 0),
            },
        ]
    )
    st.plotly_chart(px.bar(endpoint_counts, x="endpoint", y="count", title="Events Returned by Endpoint"), use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.subheader("/analytics/day-night")
        day_night_df = pd.DataFrame(
            [
                {"period": "day", "count": day_night_payload.get("day", 0)},
                {"period": "night", "count": day_night_payload.get("night", 0)},
            ]
        )
        st.plotly_chart(px.pie(day_night_df, names="period", values="count", hole=0.45), use_container_width=True)

        st.subheader("/analytics/clustering (grid cells)")
        grid_df = pd.DataFrame(clustering_payload.get("cells", []))
        if not grid_df.empty:
            st.plotly_chart(
                px.density_heatmap(
                    grid_df,
                    x="lon",
                    y="lat",
                    z="count",
                    histfunc="avg",
                    title="Grid-based Spatial Density",
                    color_continuous_scale="Viridis",
                ),
                use_container_width=True,
            )

    with right:
        st.subheader("/analytics/anomaly-detection")
        anomaly_df = _rows_df(anomaly_payload)
        if anomaly_df.empty:
            st.info("No anomalies for this threshold.")
        else:
            st.plotly_chart(
                px.scatter(
                    anomaly_df,
                    x="magnitude",
                    y="zscore",
                    color="depth",
                    hover_data=["event_date", "event_time", "place"],
                    title="Magnitude Outliers (Z-score)",
                ),
                use_container_width=True,
            )
            st.dataframe(anomaly_df[["event_date", "place", "magnitude", "zscore"]].head(20), use_container_width=True)

        st.subheader("/analytics/predictive-earthquake")
        pred_df = pd.DataFrame(pred_payload.get("predictions", []))
        if not pred_df.empty:
            st.plotly_chart(px.line(pred_df, x="date", y="predicted_earthquakes", markers=True), use_container_width=True)

    st.subheader("/analytics/ml-clustering (DBSCAN-like clustering)")
    ml_rows_df = _rows_df(ml_cluster_payload)
    if not ml_rows_df.empty:
        cluster_summary = pd.DataFrame(ml_cluster_payload.get("clusters", []))
        summary_cols = st.columns(3)
        summary_cols[0].metric("Total Points", ml_cluster_payload.get("total_points", 0))
        summary_cols[1].metric("Noise Points", ml_cluster_payload.get("noise_points", 0))
        summary_cols[2].metric("Cluster Labels", max(0, len(cluster_summary[cluster_summary["cluster_id"] >= 0])))

        fig = px.scatter_geo(
            ml_rows_df,
            lat="latitude",
            lon="longitude",
            color=ml_rows_df["cluster_id"].astype(str),
            hover_name="place",
            hover_data=["magnitude", "depth", "event_date"],
            title="ML Cluster Assignment by Epicenter",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.plotly_chart(
            px.bar(cluster_summary, x="cluster_id", y="count", title="Points per Cluster ID"),
            use_container_width=True,
        )

    st.markdown("### How machine learning is used in this project")
    st.info(
        """
- **Anomaly Detection** (`/analytics/anomaly-detection`): computes Z-scores of magnitudes and flags outliers above a threshold.
- **Predictive Modeling** (`/analytics/predictive-earthquake`): fits a simple linear trend (NumPy `polyfit`) on daily event counts and extrapolates future counts.
- **ML Clustering** (`/analytics/ml-clustering`): uses a DBSCAN-style density clustering implemented in code with `eps` and `min_samples`.

These methods are lightweight, interpretable baselines suitable for demonstrating analytical workflows in an advanced database systems project.
        """
    )


if __name__ == "__main__":
    main()
