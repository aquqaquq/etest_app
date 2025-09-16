# MyApp Dev Scaffold (React + Flask) — with Device Lookup

## Prereqs
- Node 18+
- Python 3.10+
- A C compiler (gcc/clang)

## Frontend (Vite + React)
```bash
cd frontend
npm i
npm run dev
# → http://mnplvetest01:5173  (or http://localhost:5173)
```

## Backend (Flask API) — port 8080
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Build example C binary
mkdir -p bin
cc csrc/sum.c -O2 -o bin/sum

# Optional: set your DB; defaults to SQLite file ./devices.db
# export DATABASE_URL='postgresql+psycopg2://user:pass@host:5432/dbname'
# export DATABASE_URL='mysql+pymysql://user:pass@host:3306/dbname'

# Run the API
FLASK_APP=app.py flask run -p 8080 --host 0.0.0.0
# Health: http://mnplvetest01:8080/api/health
```

## Device Lookup
- Endpoint: `POST /api/devices/search` with JSON `{ "name": "partial or full name" }`
- Returns: `{ "rows": [ { "id": 1, "name": "alpha", "status": "active" }, ... ] }`
- For dev on SQLite, the table is auto-created with a few seeded rows.

## Frontend wiring
- Page: **DeviceLookup** at `/devices` with a simple form + results table.
- Config: `frontend/.env.local` controls API base (already set to `http://mnplvetest01:8080`).

## Notes
- Production DB drivers (psycopg2/pymysql/pyodbc) are *not* included here; add per your target DB.
- SQLAlchemy is used with bound parameters to avoid injection and to stay portable across databases.
