import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_ORGANIZATION_ID: str = os.getenv("OPENAI_ORGANIZATION_ID", "")
    OPENAI_PROJECT_ID: str = os.getenv("OPENAI_PROJECT_ID", "")
    
    # App settings
    APP_NAME: str = "Recipe Extractor API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # File upload settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_TYPES: set = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    ALLOWED_VIDEO_TYPES: set = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"}
    
    # Processing settings
    GPT_MODEL: str = "gpt-4o-mini"
    GPT_TRANSCRIPT_MODEL: str = "gpt-4o-mini-transcribe"
    GPT_MAX_TOKENS: int = 1000
    GPT_TEMPERATURE: float = 0.3
    
    MAX_WORKERS: int = 4
    # CORS settings
    CORS_ORIGINS: list = ["*"]  # Configure properly for production
    
    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_PUBLISHABLE_KEY", 
            "OPENAI_API_KEY",
            "OPENAI_ORGANIZATION_ID",
            "OPENAI_PROJECT_ID"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Create settings instance
settings = Settings() 