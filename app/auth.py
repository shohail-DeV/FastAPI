import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str, expires_minutes: int | None = None) -> str:
    secret_key = os.getenv("SECRET_KEY", "change-me")
    algorithm = os.getenv("ALGORITHM", "HS256")
    default_expires = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    minutes = expires_minutes if expires_minutes is not None else default_expires

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=minutes)

    to_encode: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": expire,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    secret_key = os.getenv("SECRET_KEY", "change-me")
    algorithm = os.getenv("ALGORITHM", "HS256")
    return jwt.decode(token, secret_key, algorithms=[algorithm])
