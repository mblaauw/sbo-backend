"""
Centralized configuration module for SBO services.
"""

import logging
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("sbo.config")


class DatabaseSettings(BaseSettings):
    """Database connection settings"""
    url: str = Field(
        default="sqlite:///./sbo_dev.db",
        env="DATABASE_URL"
    )
    pool_size: int = Field(
        default=20,
        env="DATABASE_POOL_SIZE"
    )
    max_overflow: int = Field(
        default=10,
        env="DATABASE_MAX_OVERFLOW"
    )
    pool_recycle: int = Field(
        default=300,
        env="DATABASE_POOL_RECYCLE"
    )  # 5 minutes


class SecuritySettings(BaseSettings):
    """Security and authentication settings"""
    jwt_secret_key: str = Field(
        default="dev_secret_key",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        env="JWT_ALGORITHM"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )


class ServiceSettings(BaseSettings):
    """Service configuration settings"""
    host: str = Field(
        default="0.0.0.0",
        env="SERVICE_HOST"
    )
    port: int = Field(
        default=8800,
        env="SERVICE_PORT"
    )
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL"
    )
    enable_cors: bool = Field(
        default=True,
        env="ENABLE_CORS"
    )
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    environment: str = Field(
        default="development",
        env="ENVIRONMENT"
    )
    debug: bool = Field(
        default=False,
        env="DEBUG"
    )


class LLMSettings(BaseSettings):
    """LLM integration settings"""
    api_key: Optional[str] = Field(
        default=None,
        env="LLM_API_KEY"
    )
    timeout_seconds: int = Field(
        default=10,
        env="LLM_TIMEOUT_SECONDS"
    )


class Settings(BaseSettings):
    """
    Combined settings for all SBO services.
    Settings can be overridden through environment variables.
    """
    app_name: str = Field(
        default="sbo-service",
        env="APP_NAME"
    )
    app_version: str = Field(
        default="0.1.0",
        env="APP_VERSION"
    )

    database: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    service: ServiceSettings = ServiceSettings()
    llm: LLMSettings = LLMSettings()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    This ensures that settings are loaded only once.

    Returns:
        Settings instance
    """
    settings = Settings()

    # Configure log level
    log_level = getattr(logging, settings.service.log_level)
    logging.getLogger().setLevel(log_level)

    # Log settings in debug mode
    if settings.service.debug:
        settings_dict = {
            k: v for k, v in settings.dict().items()
            if k != "llm" and k != "security"
        }
        logger.debug(f"Loaded settings: {settings_dict}")

    return settings
