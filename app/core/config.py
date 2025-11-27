"""
Application configuration management
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str
    SUPABASE_SECRET_KEY: str

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_ORGANIZATION_ID: str
    OPENAI_PROJECT_ID: str

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "Recipe App API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8081"

    # OAuth & Auth Redirects
    OAUTH_REDIRECT_URL: str = "http://localhost:3000/auth/callback"
    SITE_URL: str = "http://localhost:3000"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    EXTRACTION_RATE_LIMIT_PER_MINUTE: int = 10  # Stricter limit for heavy extraction operations

    # Whisper Model
    WHISPER_MODEL: str = "base"  # Options: tiny, base, small, medium, large

    # Uvicorn Workers (0 = auto-calculate based on CPU cores)
    UVICORN_WORKERS: int = 0

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
