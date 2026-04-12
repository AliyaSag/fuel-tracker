# Fuel Tracker

Fuel Tracker is a small web app for storing refueling history and calculating fuel consumption statistics.

## Quick Start

All commands should be executed from the project root (`fuel-tracker`). Make sure you have [Poetry](https://python-poetry.org/) installed.

### 1. Install dependencies
```bash
poetry install
```

### 2. Start the Backend (API)
Open the first terminal and start the API server:
```bash
poetry run uvicorn fuel_tracker.main:app --app-dir src --reload
```
The backend will be available at: `http://127.0.0.1:8000`

### 3. Start the Frontend (UI)
Open a second terminal (while keeping the first one running) and start the UI:
```bash
poetry run streamlit run frontend/python/app.py
```
The frontend will automatically open in your browser at: `http://localhost:8501`

---

## Project Structure

### Backend (FastAPI + SQLite)
Provides a REST API for managing records:
- `POST /api/refuelings` — add a new refueling record
- `GET /api/refuelings` — get history with calculated consumption
- `GET /api/refuelings/{id}` — get a specific record
- `DELETE /api/refuelings/{id}` — delete a record
- `GET /api/stats` — get dashboard metrics
- `GET /api/health` — health check

The API supports lightweight device identification without full registration:
- If the `X-Device-Id` header is provided, it is used.
- Otherwise, it checks for the `fuel_tracker_device_id` cookie.
- If neither is present, a new device ID is generated and returned as a cookie.

### Frontend (Streamlit)
Implements a CQRS dashboard:
- **Query**: reads status, history, and aggregated stats from the API.
- **Command**: creates and deletes refueling records.

*Note: By default, the frontend expects the backend at `http://127.0.0.1:8000`. If the backend is running on a different port/host, set the `FUEL_TRACKER_API_BASE_URL=http://...` environment variable before starting the frontend.*

## Advanced

Changing the database path:
```bash
# For Linux / macOS
export FUEL_TRACKER_DB_PATH=./data/fuel_tracker.db

# For Windows (PowerShell)
$env:FUEL_TRACKER_DB_PATH="./data/fuel_tracker.db"
```

## Quality checks

```bash
poetry run flake8 src/ frontend/
poetry run bandit -r src/ frontend/
poetry run pytest --cov=src --cov=frontend --cov-report=term --cov-fail-under=70
poetry run radon cc -a -s src/ frontend/
poetry run locust -f tests/locustfile.py --headless -u 10 -r 2 -t 30s --host http://localhost:8000 --only-summary
```
