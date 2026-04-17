from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from . import schemas, crud
from .auth import create_access_token, decode_access_token
import os
from sqlalchemy import inspect, text
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Docker App")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
templates = Jinja2Templates(directory="app/templates")

ACCESS_TOKEN_COOKIE_NAME = "access_token"

# Minimal schema upgrade for existing DB volumes (no Alembic here).
@app.on_event("startup")
def _ensure_users_has_hashed_password_column():
    try:
        inspector = inspect(engine)
        if not inspector.has_table("users"):
            return
        col_names = {c["name"] for c in inspector.get_columns("users")}
        if "hashed_password" in col_names:
            return
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) NULL"))
    except Exception:
        # If this fails, normal requests will still work for fresh DBs.
        # Existing DBs may require `docker compose down -v` to recreate tables.
        pass

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _token_from_request(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip() or None
    return request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return crud.get_users(db)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = _token_from_request(request)
    if not token:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        jti = payload.get("jti")
        if not subject:
            raise credentials_exception
        if not jti:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    if crud.is_token_revoked(db, jti=jti):
        raise credentials_exception

    user = crud.get_user_by_email(db, subject)
    if not user:
        raise credentials_exception
    return user


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm uses "username" field; in this app we treat it as email
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register", response_model=schemas.UserResponse)
def auth_register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)


@app.post("/auth/login", response_model=schemas.Token)
def auth_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return login_for_access_token(form_data=form_data, db=db)


@app.post("/auth/logout")
def auth_logout(request: Request, db: Session = Depends(get_db)):
    token = _token_from_request(request)
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    try:
        payload = decode_access_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or not exp:
            raise ValueError("missing jti/exp")
        expires_at = datetime.fromtimestamp(int(exp), tz=timezone.utc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token")

    if not crud.is_token_revoked(db, jti=jti):
        crud.revoke_token(db, jti=jti, expires_at=expires_at)
    return {"detail": "Logged out"}


@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user=Depends(get_current_user)):
    return current_user


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request=request, db=db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)
    users = crud.get_users(db)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": user, "users": users},
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = crud.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password"},
            status_code=401,
        )
    token = create_access_token(subject=user.email)
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
    )
    return resp


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register")
def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = crud.get_user_by_email(db, email)
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email already registered"},
            status_code=400,
        )
    crud.create_user(db, schemas.UserCreate(name=name, email=email, password=password))
    token = create_access_token(subject=email)
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
    )
    return resp


@app.post("/logout")
def logout_ui(request: Request, db: Session = Depends(get_db)):
    # Revoke (best effort), then clear cookie.
    token = _token_from_request(request)
    if token:
        try:
            payload = decode_access_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp and not crud.is_token_revoked(db, jti=jti):
                expires_at = datetime.fromtimestamp(int(exp), tz=timezone.utc)
                crud.revoke_token(db, jti=jti, expires_at=expires_at)
        except Exception:
            pass
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(ACCESS_TOKEN_COOKIE_NAME)
    return resp