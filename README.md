# Advance Database Systems

## Overview
Advance Database Systems is an earthquake analytics platform that ingests seismic event data and exposes analytics APIs for magnitude filtering, date-range analysis, geospatial distance checks, day/night event distribution, and grid-based clustering.

## Codebase Audit Report
### Languages
- Python (Flask API, Streamlit dashboard)
- YAML (Docker Compose, CI)

### Architecture & Entry Points
- `main.py` is the application entry point.
- `app/` contains modular Flask architecture (`config`, `db`, `services`, `routes`).
- `dashboard/dashboard.py` is the observability dashboard entry point.

### Database Technologies
- SQLite (local embedded analytics store).
- CSV seed data (`all_month.csv`) is loaded on first run.

### Key Findings from Legacy Implementation
- Mixed database drivers and undefined objects (`ibm_db`, `db2cred`) caused runtime failures.
- Hardcoded credentials and duplicate imports introduced security and maintainability risks.
- Monolithic route logic prevented reuse and testing.
- No CI, type checks, or formatting/linting setup.

### Improvements Implemented
- Refactored into modular service architecture.
- Replaced broken DB integration with SQLite + indexed schema.
- Added query and geospatial services with parameterized SQL.
- Added Streamlit dashboard for system and query metrics.
- Added Docker, Docker Compose, and GitHub Actions CI.
- Added black/flake8/mypy/pytest quality pipeline.

## Features
- REST analytics endpoints for:
  - Magnitude threshold counts
  - Magnitude/date range filters
  - Radius-based geospatial lookup
  - Day vs night event distribution
  - Grid clustering analytics
- Automatic CSV-to-database bootstrapping
- Performance indexes for common query filters
- Streamlit monitoring dashboard with interactive charts

## Architecture
- **API Layer**: Flask routes in `app/routes.py`
- **Service Layer**: Query/business logic in `app/services.py`
- **Data Layer**: SQLite initialization and seed loading in `app/db.py`
- **Dashboard Layer**: Streamlit + Plotly charts in `dashboard/dashboard.py`

## Tech Stack
**Backend**
- Python 3.11
- Flask

**Database**
- SQLite

**Tools**
- Docker / Docker Compose
- GitHub Actions CI
- black, flake8, mypy, pytest
- Streamlit + Plotly

## Installation
1. Clone repository:
   ```bash
   git clone https://github.com/vrajpatell/Advance-Database-Systems.git
   cd Advance-Database-Systems
   ```
2. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. (Optional) Install developer tools:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Configure environment variables (optional):
   - `PORT` (default: `5000`)
   - `DATABASE_PATH` (default: `data/earthquakes.db`)
   - `SOURCE_CSV` (default: `all_month.csv`)
5. Start the application:
   ```bash
   python main.py
   ```

## Usage
### API
- Health check: `GET /health`
- Run analytics with JSON payloads:
  - `POST /analytics/count-by-magnitude`
  - `POST /analytics/range`
  - `POST /analytics/distance`
  - `POST /analytics/day-night`
  - `POST /analytics/clustering`

### Dashboard
```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/dashboard.py
```

## Project Structure
```text
app/
  __init__.py
  config.py
  db.py
  routes.py
  services.py
dashboard/
  dashboard.py
  requirements.txt
tests/
  test_app.py
.github/workflows/
  ci.yml
main.py
Dockerfile
docker-compose.yml
```

## Deployment
### Docker
```bash
docker build -t advance-db-systems .
docker run -p 5000:5000 advance-db-systems
```

### Docker Compose
```bash
docker compose up --build
```

## Dashboard
The Streamlit dashboard provides:
- database query performance visualization
- records processed KPI
- system health indicator
- API latency trend chart
- transaction metric distribution

## Render Deployment
This repository is now configured for Render with `render.yaml` and production process settings.

### Option A: Blueprint deploy (recommended)
1. Push code to GitHub.
2. In Render, choose **New +** → **Blueprint** and select this repository.
3. Render will create:
   - `advance-db-api` (Flask/Gunicorn API)
   - `advance-db-dashboard` (Streamlit dashboard)

### Option B: Manual service deploy
- **API service**
  - Build command: `pip install -r requirements.txt`
  - Start command: `gunicorn main:app --bind 0.0.0.0:$PORT`
- **Dashboard service**
  - Build command: `pip install -r requirements.txt -r dashboard/requirements.txt`
  - Start command: `streamlit run dashboard/dashboard.py --server.port $PORT --server.address 0.0.0.0`

> Note: Render free instances use ephemeral disk. SQLite data is recreated from `all_month.csv` on restart.

## Contributing
1. Fork the repository
2. Create a feature branch
3. Run checks: `black --check .`, `flake8 .`, `mypy app main.py`, `pytest`
4. Open a pull request with a clear description and tests

## License
MIT License

## GitHub Metadata Suggestions
- **Description (≤160 chars):**
  `Earthquake analytics platform with Flask APIs, SQLite query optimization, Streamlit monitoring dashboard, and production-ready CI/CD tooling.`
- **Topics/Tags:**
  `database-systems`, `flask`, `sqlite`, `streamlit`, `data-analytics`, `geospatial`, `docker`, `github-actions`
- **Suggested Banner:**
  A dark world map heatmap of earthquake intensity with overlayed system metrics cards (latency, throughput, health).
