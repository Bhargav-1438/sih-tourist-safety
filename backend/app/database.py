"""
SQLAlchemy database setup.

Configures the engine, session factory and declarative base used by the
application's ORM models. No models are defined here yet; they will be added
as features are implemented.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import DATABASE_URL

# SQLite needs check_same_thread=False so the connection can be shared across
# FastAPI's worker threads.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# The engine is created lazily; no connection is opened at import time, which
# keeps startup (and /health) independent of the database.
engine = create_engine(DATABASE_URL, connect_args=_connect_args)

# SessionLocal is a factory for short-lived database sessions, one per request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models.
Base = declarative_base()


def get_db() -> Session:
    """FastAPI dependency yielding a database session, closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
