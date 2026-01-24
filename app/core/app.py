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

    # Start popular recipes cache refresh scheduler (every 4 hours)
    from app.core.cache_refresh import start_cache_refresh_scheduler
    cache_refresh_scheduler = start_cache_refresh_scheduler(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SECRET_KEY,
        interval_hours=4
    )

    # Start push notification scheduler
    from app.core.notification_scheduler import start_notification_scheduler
    notification_scheduler = start_notification_scheduler(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SECRET_KEY
    )

    logger.info("Application startup complete")

    yield

    # Shutdown
    if cleanup_scheduler:
        cleanup_scheduler.shutdown(wait=False)
        logger.info("Cleanup scheduler stopped")

    if cache_refresh_scheduler:
        cache_refresh_scheduler.shutdown(wait=False)
        logger.info("Cache refresh scheduler stopped")

    if notification_scheduler:
        notification_scheduler.shutdown(wait=False)
        logger.info("Notification scheduler stopped")

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

    # CORS Middleware - Development allows common localhost ports
    if settings.is_production:
        cors_origins = settings.cors_origins_list
    else:
        # In development, allow common localhost ports + configured origins
        cors_origins = list(set([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8080",
            "http://localhost:8081",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8081",
        ] + settings.cors_origins_list))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
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
