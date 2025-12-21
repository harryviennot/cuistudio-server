"""
FastAPI application factory
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import sentry_sdk

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.events import init_event_broadcaster, shutdown_event_broadcaster
from app.core.rate_limit import RateLimitMiddleware
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)

# Initialize Sentry before app creation
settings = get_settings()
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        send_default_pii=True,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    settings = get_settings()

    # Startup
    setup_logging()
    logger.info("Initializing event broadcaster...")
    await init_event_broadcaster()

    # Start temp video cleanup scheduler
    from app.core.cleanup import start_cleanup_scheduler
    cleanup_scheduler = start_cleanup_scheduler(
        temp_dir=settings.TEMP_VIDEO_DIR,
        max_age_hours=settings.TEMP_VIDEO_MAX_AGE_HOURS,
        interval_hours=settings.TEMP_VIDEO_CLEANUP_INTERVAL_HOURS
    )

    logger.info("Application startup complete")

    yield

    # Shutdown
    if cleanup_scheduler:
        cleanup_scheduler.shutdown(wait=False)
        logger.info("Cleanup scheduler stopped")

    logger.info("Shutting down event broadcaster...")
    await shutdown_event_broadcaster()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
    )

    # Rate Limiting Middleware (added first, processed last in middleware chain)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
        extraction_per_minute=settings.EXTRACTION_RATE_LIMIT_PER_MINUTE
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        }

    return app
