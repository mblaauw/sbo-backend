# services/database.py
"""
Database connection and session management for SBO services.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging
from services.config import get_settings

logger = logging.getLogger("sbo.database")

# Get settings
settings = get_settings()

# Create SQLAlchemy engine with connection pooling settings
logger.info(f"Setting up database connection: {settings.DATABASE_URL.split('@')[-1]}")
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=settings.DATABASE_POOL_RECYCLE
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Database dependency for FastAPI endpoints
def get_db():
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

# Context manager for database operations outside of FastAPI endpoints
@contextmanager
def get_db_context():
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
        
def init_db():
    """Initialize database tables"""
    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)
    
def drop_db():
    """Drop all database tables (use with caution)"""
    logger.warning("Dropping all database tables!")
    Base.metadata.drop_all(bind=engine)