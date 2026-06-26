import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
from .config import settings

def get_database_url() -> str:
    if settings.TURSO_DATABASE_URL and settings.TURSO_AUTH_TOKEN:
        # Normalize URL scheme for sqlalchemy-libsql (requires sqlite+libsql://)
        clean_url = settings.TURSO_DATABASE_URL
        if clean_url.startswith("https://"):
            clean_url = clean_url[8:]
        elif clean_url.startswith("http://"):
            clean_url = clean_url[7:]
        elif clean_url.startswith("libsql://"):
            clean_url = clean_url[9:]
        
        return f"sqlite+libsql://{clean_url}?secure=true"
    else:
        # Offline Fallback to Local SQLite
        DB_DIR = "./data"
        os.makedirs(DB_DIR, exist_ok=True)
        return f"sqlite:///{DB_DIR}/learning.db"

SQLALCHEMY_DATABASE_URL = get_database_url()

if settings.TURSO_DATABASE_URL and settings.TURSO_AUTH_TOKEN:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={
            "auth_token": settings.TURSO_AUTH_TOKEN,
        }
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
