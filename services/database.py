from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from contextlib import contextmanager

# Get database URL from environment or use a default for development
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sbo_user:sbo_password@postgres:5432/sbo_db")

# Create SQLAlchemy engine with connection pooling settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300  # Recycle connections every 5 minutes
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Database dependency for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Context manager for database operations outside of FastAPI endpoints
@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Function to initialize database tables
def init_db():
    Base.metadata.create_all(bind=engine)
    
# Function to drop all tables (use with caution)
def drop_db():
    Base.metadata.drop_all(bind=engine)