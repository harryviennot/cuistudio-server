"""
Main FastAPI application entry point
"""
import uvicorn
from app.core.app import create_app
from app.core.config import get_settings

settings = get_settings()
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
