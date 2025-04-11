"""
Database connection and session management for SBO services.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging
from typing import Generator
from config import get_settings

logger = logging.getLogger("sbo.database")

# Get settings
settings = get_settings()

# Create SQLAlchemy engine with connection pooling settings
engine_url = settings.database.url
if engine_url.startswith("sqlite:"):
    # SQLite-specific settings
    engine = create_engine(
        engine_url,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )

    # Add pragmas for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL or other database settings
    engine = create_engine(
        engine_url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_pre_ping=True,
        pool_recycle=settings.database.pool_recycle
    )

logger.info(f"Database engine configured: {engine_url.split('@')[-1]}")

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get a database session.

    Yields:
        SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database operations outside of FastAPI endpoints.

    Yields:
        SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize database tables"""
    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)

def drop_db() -> None:
    """Drop all database tables (use with caution)"""
    logger.warning("Dropping all database tables!")
    Base.metadata.drop_all(bind=engine)
