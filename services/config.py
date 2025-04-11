# services/config.py
"""
Centralized configuration module for SBO services.
"""

import os
import logging
from pydantic import BaseSettings, PostgresDsn, validator
from typing import Dict, Any, Optional, List
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sbo.config")

class ServiceSettings(BaseSettings):
    """
    Common settings for all SBO services.
    
    Settings can be overridden through environment variables.
    For example, to set DATABASE_URL, use the environment variable DATABASE_URL.
    """
    # Application settings
    APP_NAME: str = "sbo-service"
    APP_VERSION: str = "0.1.0"
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://sbo_user:sbo_password@postgres:5432/sbo_db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "300"))  # 5 minutes

    # CORS settings
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev_secret_key")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Service URLs
    API_GATEWAY_URL: str = os.getenv("API_GATEWAY_URL", "http://api-gateway:8800")
    SKILLS_SERVICE_URL: str = os.getenv("SKILLS_SERVICE_URL", "http://skills-service:8800")
    MATCHING_SERVICE_URL: str = os.getenv("MATCHING_SERVICE_URL", "http://matching-service:8800")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://user-service:8800")
    ASSESSMENT_SERVICE_URL: str = os.getenv("ASSESSMENT_SERVICE_URL", "http://assessment-service:8800")
    LLM_SERVICE_URL: str = os.getenv("LLM_SERVICE_URL", "http://llm-service:8800")
    
    # LLM settings
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY")
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "10"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t", "yes")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator("DATABASE_URL")
    def check_db_url(cls, v):
        # Check if we need to convert SQLite URL for SQLAlchemy 1.4+
        if v.startswith("sqlite:"):
            logger.info("Using SQLite database")
            return v.replace("sqlite:", "sqlite+pysqlite:")
        logger.info("Using PostgreSQL database")
        return v

@lru_cache()
def get_settings() -> ServiceSettings:
    """
    Get cached settings instance.
    This ensures that settings are loaded only once.
    
    Returns:
        Settings instance
    """
    settings = ServiceSettings()
    
    # Log all settings once at startup
    if settings.DEBUG:
        settings_dict = {k: v for k, v in settings.dict().items() if k != "LLM_API_KEY" and k != "JWT_SECRET_KEY"}
        logger.debug(f"Loaded settings: {settings_dict}")
    
    # Configure log level
    logging.getLogger().setLevel(getattr(logging, settings.LOG_LEVEL))
    
    return settings