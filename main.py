"""
Main FastAPI application entry point
"""
import multiprocessing
import uvicorn
from app.core.app import create_app
from app.core.config import get_settings

settings = get_settings()
app = create_app()

if __name__ == "__main__":
    if settings.DEBUG:
        # Development: single worker with hot reload
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            log_level=settings.LOG_LEVEL.lower()
        )
    else:
        # Production: multiple workers, no reload
        # Use configured workers or auto-calculate based on CPU cores
        workers = settings.UVICORN_WORKERS or (multiprocessing.cpu_count() * 2) + 1
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            workers=workers,
            reload=False,
            log_level=settings.LOG_LEVEL.lower()
        )
