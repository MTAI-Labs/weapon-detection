import os
from typing import Optional, List, Dict, Any
from pydantic import AnyHttpUrl, field_validator, model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "weapon-detection"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS origins - use Field to prevent pydantic-settings JSON parsing
    BACKEND_CORS_ORIGINS: str = "localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        """Convert CORS origins string to list"""
        if not self.BACKEND_CORS_ORIGINS:
            return []
        if self.BACKEND_CORS_ORIGINS.startswith("[") and self.BACKEND_CORS_ORIGINS.endswith("]"):
            # Handle JSON-like list string
            import json
            try:
                return json.loads(self.BACKEND_CORS_ORIGINS)
            except (json.JSONDecodeError, ValueError):
                pass
        # Comma-separated values
        return [i.strip() for i in self.BACKEND_CORS_ORIGINS.split(",") if i.strip()]
    
    # Database settings - PostgreSQL optimized
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "api_user"
    POSTGRES_PASSWORD: str = "api_password"
    POSTGRES_DB: str = "api_db"
    
    # Database URL construction
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Database settings - PostgreSQL optimized
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "api_user"
    POSTGRES_PASSWORD: str = "api_password"
    POSTGRES_DB: str = "api_db"
    
    # Database connection pool settings (kept for compatibility but not used with async engines)
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_POOL_PRE_PING: bool = True
    
    # Database URL construction
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ALGORITHM: str = "HS256"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    @model_validator(mode="before")
    @classmethod
    def validate_settings(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Assemble database connection if not provided
        if not isinstance(values.get("SQLALCHEMY_DATABASE_URI"), str):
            if "SQLALCHEMY_DATABASE_URI" not in values:
                postgres_user = values.get("POSTGRES_USER")
                postgres_password = values.get("POSTGRES_PASSWORD")
                postgres_server = values.get("POSTGRES_SERVER")
                postgres_port = values.get("POSTGRES_PORT", 5432)
                postgres_db = values.get("POSTGRES_DB")
                
                values["SQLALCHEMY_DATABASE_URI"] = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"
        
        # Set debug mode based on environment
        if "DEBUG" not in values:
            environment = values.get("ENVIRONMENT", "production")
            values["DEBUG"] = environment.lower() in ["development", "dev"]
        
        return values
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Redis (optional for caching)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_ignore_empty=True,
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()