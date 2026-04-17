from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
from . import models, schemas
from .auth import hash_password, verify_password

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session):
    return db.query(models.User).all()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def revoke_token(db: Session, *, jti: str, expires_at: datetime):
    db_obj = models.RevokedToken(jti=jti, expires_at=expires_at)
    db.add(db_obj)
    db.commit()
    return db_obj


def is_token_revoked(db: Session, *, jti: str) -> bool:
    stmt = select(models.RevokedToken.jti).where(models.RevokedToken.jti == jti)
    return db.execute(stmt).first() is not None