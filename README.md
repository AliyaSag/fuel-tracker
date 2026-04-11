# fuel-tracker

Fuel Tracker is a small web app for storing refueling history and
calculating fuel consumption statistics.

## Backend

The backend is built with FastAPI and SQLite. It provides:

- `POST /api/refuelings` to add a refueling
- `GET /api/refuelings` to list history with calculated consumption
- `GET /api/refuelings/{id}` to fetch a single record
- `DELETE /api/refuelings/{id}` to remove a record
- `GET /api/stats` to fetch dashboard metrics
- `GET /api/health` for a health check

The API also supports lightweight device identity without full
authentication:

- If `X-Device-Id` header is provided, the request uses that identity.
- Otherwise, if `fuel_tracker_device_id` cookie exists, it is reused.
- Otherwise, the backend generates a new device id, completes the same
  request, and sets the cookie in the response.

## Run locally

Install dependencies with Poetry:

```bash
poetry install
```

Start the API:

```bash
poetry run uvicorn fuel_tracker.main:app --app-dir src --reload
```

Optional database path:

```bash
FUEL_TRACKER_DB_PATH=./data/fuel_tracker.db
```

## Quality checks

```bash
poetry run flake8 src/
poetry run bandit -r src/
poetry run pytest --cov=src --cov-report=term --cov-fail-under=70
poetry run radon cc -a -s src/
```
