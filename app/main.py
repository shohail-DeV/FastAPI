from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from . import schemas, crud
import os

from dotenv import load_dotenv
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Docker App")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "FastAPI + MySQL + Docker is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return crud.get_users(db)