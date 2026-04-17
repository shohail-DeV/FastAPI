from sqlalchemy import Column, DateTime, Integer, String
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    # Nullable for simple "no-migrations" upgrades; new users always set it.
    hashed_password = Column(String(255), nullable=True)


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(String(64), primary_key=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)