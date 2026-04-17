# FastAPI + MySQL + Docker (Auth + CRUD example)

Small FastAPI app containerized with Docker, backed by MySQL 8 (via `docker-compose`).

It includes:
- A simple **server-rendered UI** (login, register, dashboard homepage)
- **OAuth2 Password flow** issuing **JWT access tokens**
- Minimal **User CRUD** (create + list) using SQLAlchemy

## What’s inside

- **API**: FastAPI + Uvicorn
- **UI**: Jinja2 templates (server-rendered pages)
- **DB**: MySQL 8 (Compose service: `db`)
- **ORM**: SQLAlchemy (creates tables at startup)
- **Config**: Environment variables from `.env` (loaded both by Compose and the app)

## Project structure

```
.
├─ app/
│  ├─ main.py        # API + UI routes
│  ├─ auth.py        # password hashing + JWT helpers
│  ├─ database.py    # SQLAlchemy engine/session
│  ├─ models.py      # DB models (User, revoked tokens)
│  ├─ schemas.py     # Pydantic schemas
│  └─ crud.py        # DB operations
│  └─ templates/     # HTML templates (login/register/home)
├─ Dockerfile
├─ docker-compose.yml
├─ entrypoint.sh     # waits for DB, then starts uvicorn
└─ requirements.txt
```

## Routes

### UI routes (browser)

- `GET /` → **dashboard** (requires login; otherwise redirects to `/login`)
- `GET /login` → login page
- `POST /login` → sets JWT into an **HttpOnly cookie**, then redirects to `/`
- `GET /register` → register page
- `POST /register` → creates user, sets cookie, then redirects to `/`
- `POST /logout` → revokes token (best-effort) and clears cookie

### API routes (JSON)

- `GET /health` → `{ "status": "healthy" }`
- `POST /users/` → create a user (now includes `password`)
- `GET /users/` → list users
- `POST /token` → OAuth2 Password flow token endpoint (returns JWT, for Swagger OAuth2)
- `POST /auth/register` → register
- `POST /auth/login` → login (same behavior as `/token`)
- `POST /auth/logout` → logout (revokes current JWT; requires `Authorization: Bearer <token>`)
- `GET /users/me` → protected endpoint (works with `Authorization: Bearer <token>` OR cookie)

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

# JWT settings (OAuth2 Password Flow)
# IMPORTANT: choose a long random secret in real deployments
SECRET_KEY=change-me-please
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
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

### UI flow (browser)

1) Open `http://localhost:8000/` → you’ll be redirected to `/login`
2) Register or login → you’ll land on the dashboard homepage
3) Click **Logout** to end session

### Create a user

```bash
curl -X POST "http://localhost:8000/users/" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Ada Lovelace\",\"email\":\"ada@example.com\",\"password\":\"secret123\"}"
```

### Login (get JWT)

```bash
curl -X POST "http://localhost:8000/token" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=ada@example.com&password=secret123"
```

### Call protected endpoint (JWT)

```bash
curl "http://localhost:8000/users/me" ^
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN_HERE>"
```

### Register / Login / Logout (auth routes)

Register:

```bash
curl -X POST "http://localhost:8000/auth/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Ada Lovelace\",\"email\":\"ada@example.com\",\"password\":\"secret123\"}"
```

Login:

```bash
curl -X POST "http://localhost:8000/auth/login" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=ada@example.com&password=secret123"
```

Logout:

```bash
curl -X POST "http://localhost:8000/auth/logout" ^
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN_HERE>"
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
- **Logout behavior**: JWTs are stateless; logout is implemented by storing a revoked token id (`jti`) in MySQL and rejecting it on subsequent requests.

