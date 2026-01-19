"""
Application configuration management
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str
    SUPABASE_SECRET_KEY: str

    # OpenAI (kept for Whisper transcription)
    OPENAI_API_KEY: str
    OPENAI_ORGANIZATION_ID: str
    OPENAI_PROJECT_ID: str

    # Google Gemini (for recipe extraction)
    GOOGLE_API_KEY: Optional[str] = None

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "Recipe App API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: Optional[str] = None

    # OAuth & Auth Redirects
    OAUTH_REDIRECT_URL: str = "http://localhost:3000/auth/callback"
    SITE_URL: str = "http://localhost:3000"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50

    # Temp Video Storage (for Instagram client-side downloads)
    TEMP_VIDEO_DIR: str = "temp/videos"
    TEMP_VIDEO_MAX_AGE_HOURS: int = 2
    TEMP_VIDEO_CLEANUP_INTERVAL_HOURS: int = 1

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    EXTRACTION_RATE_LIMIT_PER_MINUTE: int = 10  # Stricter limit for heavy extraction operations

    # Whisper Model
    WHISPER_MODEL: str = "base"  # Options: tiny, base, small, medium, large

    # Uvicorn Workers (0 = auto-calculate based on CPU cores)
    UVICORN_WORKERS: int = 0

    # Logging
    LOG_LEVEL: str = "INFO"

    # Sentry
    SENTRY_DSN: Optional[str] = None

    # RevenueCat
    REVENUECAT_WEBHOOK_SECRET: Optional[str] = None
    REVENUECAT_API_KEY: Optional[str] = None  # Secret API key for fetching customer info
    REVENUECAT_PROJECT_ID: Optional[str] = None  # Project ID from RevenueCat dashboard

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars not defined in Settings
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
