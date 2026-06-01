"""Koneksi database PostgreSQL (SQLAlchemy)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    """Dependency FastAPI: sesi DB per-request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
