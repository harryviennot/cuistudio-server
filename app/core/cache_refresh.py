"""
Cache refresh service for materialized views.

Handles automatic refresh of the popular_recipes_mv materialized view
every 4 hours to keep popularity rankings up-to-date without
recalculating on every API request.
"""
import logging

logger = logging.getLogger(__name__)

# Default settings
REFRESH_INTERVAL_HOURS = 4


async def refresh_popular_recipes_cache(supabase_url: str, supabase_key: str) -> dict:
    """
    Refresh the popular_recipes_mv materialized view.

    Calls the PostgreSQL function refresh_popular_recipes_cache() which
    uses REFRESH MATERIALIZED VIEW CONCURRENTLY to avoid locking.

    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key

    Returns:
        Dict with refresh statistics
    """
    from supabase import create_client

    stats = {
        "success": False,
        "error": None
    }

    try:
        # Create a fresh client for the background task
        supabase = create_client(supabase_url, supabase_key)

        # Call the refresh function
        response = supabase.rpc('refresh_popular_recipes_cache').execute()

        stats["success"] = True
        logger.info("Successfully refreshed popular_recipes_mv materialized view")

    except Exception as e:
        error_msg = f"Failed to refresh popular recipes cache: {str(e)}"
        logger.error(error_msg)
        stats["error"] = error_msg

    return stats


def start_cache_refresh_scheduler(
    supabase_url: str,
    supabase_key: str,
    interval_hours: int = REFRESH_INTERVAL_HOURS
):
    """
    Start a background scheduler for periodic cache refresh.

    Uses APScheduler to refresh the popular_recipes_mv materialized view
    every interval_hours.

    Args:
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key
        interval_hours: How often to refresh (in hours, default: 4)

    Returns:
        The scheduler instance, or None if APScheduler is not available
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger
    except ImportError:
        logger.warning(
            "APScheduler not installed. Popular recipes cache will not refresh automatically. "
            "Install with: pip install apscheduler"
        )
        return None

    scheduler = AsyncIOScheduler()

    # Add the refresh job
    scheduler.add_job(
        refresh_popular_recipes_cache,
        trigger=IntervalTrigger(hours=interval_hours),
        args=[supabase_url, supabase_key],
        id="refresh_popular_recipes_cache",
        name="Refresh popular recipes materialized view",
        replace_existing=True
    )

    scheduler.start()
    logger.info(
        f"Started popular recipes cache refresh scheduler: "
        f"runs every {interval_hours} hours"
    )

    return scheduler
