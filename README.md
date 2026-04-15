# FastAPI + MySQL + Docker (CRUD example)

Small FastAPI API containerized with Docker, backed by MySQL 8 (via `docker-compose`). It exposes a health check and a minimal **User** CRUD (create + list) using SQLAlchemy.

## What’s inside

- **API**: FastAPI + Uvicorn
- **DB**: MySQL 8 (Compose service: `db`)
- **ORM**: SQLAlchemy (creates tables at startup)
- **Config**: Environment variables from `.env` (loaded both by Compose and the app)

## Project structure

```
.
├─ app/
│  ├─ main.py        # FastAPI routes
│  ├─ database.py    # SQLAlchemy engine/session
│  ├─ models.py      # DB models (User)
│  ├─ schemas.py     # Pydantic schemas
│  └─ crud.py        # DB operations
├─ Dockerfile
├─ docker-compose.yml
├─ entrypoint.sh     # waits for DB, then starts uvicorn
└─ requirements.txt
```

## API endpoints

- `GET /` → sanity message
- `GET /health` → `{ "status": "healthy" }`
- `POST /users/` → create a user
- `GET /users/` → list users

Swagger UI:
- `http://localhost:8000/docs`

## Quickstart (Docker Compose)

### 1) Create a `.env`

Create a `.env` file in the project root:

```env
# MySQL (used by the db container)
MYSQL_ROOT_PASSWORD=change-me-root
MYSQL_DATABASE=app_db
MYSQL_USER=app_user
MYSQL_PASSWORD=change-me-user

# SQLAlchemy connection string (used by the FastAPI app)
# IMPORTANT: host must be "db" (the compose service name), not localhost.
DATABASE_URL=mysql+pymysql://app_user:change-me-user@db:3306/app_db
```

### 2) Build and run

```bash
docker compose up --build
```

Services:
- **API**: `http://localhost:8000`
- **MySQL**: exposed to host on `localhost:3307` (container is `3306`)

To stop:

```bash
docker compose down
```

To stop and remove DB data:

```bash
docker compose down -v
```

## Usage examples

### Create a user

```bash
curl -X POST "http://localhost:8000/users/" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Ada Lovelace\",\"email\":\"ada@example.com\"}"
```

### List users

```bash
curl "http://localhost:8000/users/"
```

### Health check

```bash
curl "http://localhost:8000/health"
```

## Run locally (without Docker)

### Prereqs

- Python 3.11+ recommended
- A MySQL instance you can connect to (local MySQL, Docker MySQL, or managed DB)

### Steps

```bash
python -m venv .venv
```

Activate:
- PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install deps:

```bash
pip install -r requirements.txt
```

Set `DATABASE_URL` (example):

```powershell
$env:DATABASE_URL="mysql+pymysql://app_user:change-me-user@127.0.0.1:3307/app_db"
```

Run:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Notes / Troubleshooting

- **`DATABASE_URL not set`**: the container entrypoint requires `DATABASE_URL`. Ensure your root `.env` exists and includes it.
- **DB connection fails on Docker**: the hostname in `DATABASE_URL` must be `db` (Compose service), not `localhost`.
- **Port mapping**: Compose maps `3307:3306`, so from your host use port `3307`; from inside containers use `3306`.
- **Tables are created at startup**: `app/main.py` calls `Base.metadata.create_all(bind=engine)` when the app starts.

## License

Add a license if you plan to publish this project.
