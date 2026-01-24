"""
Notification Scheduler Service

Handles scheduled push notifications using APScheduler:
- First recipe nudge (hourly check for users 24h after signup with no recipes)
- Weekly credits refresh (Monday 12:00 UTC)
- Cook tonight suggestions (hourly, smart timing based on user activity)
- Miss you re-engagement (daily 18:00 UTC for 7+ days inactive)
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


async def process_first_recipe_nudge(supabase_url: str, supabase_key: str) -> Dict[str, Any]:
    """
    Send nudge to users who signed up 24h ago but haven't extracted any recipes.

    Runs hourly to catch users at appropriate times.
    """
    from supabase import create_client
    from app.services.push_notification_service import PushNotificationService, NotificationType

    stats = {"checked": 0, "sent": 0, "errors": 0}

    try:
        supabase = create_client(supabase_url, supabase_key)
        push_service = PushNotificationService(supabase)

        # Find users who:
        # - Signed up between 23-25 hours ago (to catch them in the hourly window)
        # - Have no recipes
        # - Have notification preferences enabled
        # - Haven't received this notification yet
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=25)
        window_end = now - timedelta(hours=23)

        result = supabase.rpc("get_first_recipe_nudge_eligible_users", {
            "window_start": window_start.isoformat(),
            "window_end": window_end.isoformat()
        }).execute()

        eligible_users = result.data or []
        stats["checked"] = len(eligible_users)

        for user in eligible_users:
            user_id = user["id"]
            try:
                success = await push_service.send_first_recipe_nudge(user_id)
                if success:
                    stats["sent"] += 1
            except Exception as e:
                logger.error(f"Error sending first recipe nudge to {user_id}: {e}")
                stats["errors"] += 1

        logger.info(f"First recipe nudge: checked={stats['checked']}, sent={stats['sent']}")

    except Exception as e:
        logger.error(f"Error in first_recipe_nudge job: {e}")
        stats["errors"] += 1

    return stats


async def process_weekly_credits_refresh(supabase_url: str, supabase_key: str) -> Dict[str, Any]:
    """
    Notify free tier users that their weekly credits have been refreshed.

    Runs Monday at 12:00 UTC (lunchtime).
    """
    from supabase import create_client
    from app.services.push_notification_service import PushNotificationService
    from app.services.credit_service import WEEKLY_FREE_CREDITS

    stats = {"checked": 0, "sent": 0, "errors": 0}

    try:
        supabase = create_client(supabase_url, supabase_key)
        push_service = PushNotificationService(supabase)

        # Get free tier users with push tokens who have this notification enabled
        result = supabase.rpc("get_weekly_credits_notification_users").execute()

        eligible_users = result.data or []
        stats["checked"] = len(eligible_users)

        # Send in batches
        user_ids = [u["user_id"] for u in eligible_users]

        if user_ids:
            results = await push_service.send_bulk_notifications(
                user_ids=user_ids,
                notification_type=push_service.NotificationType.WEEKLY_CREDITS_REFRESH,
                title="Your credits are ready!",
                body=f"You have {WEEKLY_FREE_CREDITS} free extractions this week. What will you cook?",
                data={"screen": "new-recipe"}
            )
            stats["sent"] = sum(1 for success in results.values() if success)

        logger.info(f"Weekly credits refresh: checked={stats['checked']}, sent={stats['sent']}")

    except Exception as e:
        logger.error(f"Error in weekly_credits_refresh job: {e}")
        stats["errors"] += 1

    return stats


async def process_cook_tonight(supabase_url: str, supabase_key: str) -> Dict[str, Any]:
    """
    Send cook tonight suggestions based on user's preferred notification time.

    Runs hourly. For each user:
    - Active users (app opened in last 7 days): Can receive daily
    - Inactive users (7+ days): Can receive weekly max

    Uses smart timing: sends 2 hours before user's typical app open time.
    """
    from supabase import create_client
    from app.services.push_notification_service import PushNotificationService

    stats = {"checked": 0, "sent": 0, "errors": 0}

    try:
        supabase = create_client(supabase_url, supabase_key)
        push_service = PushNotificationService(supabase)

        current_hour = datetime.now(timezone.utc).hour

        # Get eligible users for this hour
        # The database function handles:
        # - Checking preferred notification hour
        # - Checking last notification sent (daily for active, weekly for inactive)
        # - Checking notification preferences
        result = supabase.rpc("get_cook_tonight_eligible_users", {
            "target_hour": current_hour
        }).execute()

        eligible_users = result.data or []
        stats["checked"] = len(eligible_users)

        for user in eligible_users:
            user_id = user["user_id"]
            recipe_id = user.get("suggested_recipe_id")
            recipe_title = user.get("suggested_recipe_title", "one of your saved recipes")

            if not recipe_id:
                continue

            try:
                success = await push_service.send_cook_tonight(
                    user_id=user_id,
                    recipe_id=recipe_id,
                    recipe_title=recipe_title
                )
                if success:
                    stats["sent"] += 1
                    # Update last sent timestamp
                    supabase.table("user_activity_stats").update({
                        "last_cook_tonight_sent_at": datetime.now(timezone.utc).isoformat()
                    }).eq("user_id", user_id).execute()

            except Exception as e:
                logger.error(f"Error sending cook tonight to {user_id}: {e}")
                stats["errors"] += 1

        logger.info(f"Cook tonight: checked={stats['checked']}, sent={stats['sent']}")

    except Exception as e:
        logger.error(f"Error in cook_tonight job: {e}")
        stats["errors"] += 1

    return stats


async def process_miss_you(supabase_url: str, supabase_key: str) -> Dict[str, Any]:
    """
    Re-engage users who haven't opened the app in 7+ days.

    Runs daily at 18:00 UTC.
    """
    from supabase import create_client
    from app.services.push_notification_service import PushNotificationService

    stats = {"checked": 0, "sent": 0, "errors": 0}

    try:
        supabase = create_client(supabase_url, supabase_key)
        push_service = PushNotificationService(supabase)

        # Get users inactive for 7+ days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)

        result = supabase.rpc("get_miss_you_eligible_users", {
            "inactive_since": cutoff_date.isoformat()
        }).execute()

        eligible_users = result.data or []
        stats["checked"] = len(eligible_users)

        user_ids = [u["user_id"] for u in eligible_users]

        if user_ids:
            results = await push_service.send_bulk_notifications(
                user_ids=user_ids,
                notification_type=push_service.NotificationType.MISS_YOU,
                title="We miss you in the kitchen!",
                body="Your recipes are waiting. Come back and cook something delicious!",
                data={"screen": "library"}
            )
            stats["sent"] = sum(1 for success in results.values() if success)

        logger.info(f"Miss you: checked={stats['checked']}, sent={stats['sent']}")

    except Exception as e:
        logger.error(f"Error in miss_you job: {e}")
        stats["errors"] += 1

    return stats


def start_notification_scheduler(supabase_url: str, supabase_key: str):
    """
    Start the notification scheduler with all scheduled jobs.

    Jobs:
    - first_recipe_nudge: Every 1 hour
    - weekly_credits_refresh: Monday 12:00 UTC
    - cook_tonight: Every 1 hour
    - miss_you: Daily 18:00 UTC

    Returns:
        The scheduler instance, or None if APScheduler is not available
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning(
            "APScheduler not installed. Scheduled notifications will not run. "
            "Install with: pip install apscheduler"
        )
        return None

    scheduler = AsyncIOScheduler()

    # First recipe nudge - every hour
    scheduler.add_job(
        process_first_recipe_nudge,
        trigger=IntervalTrigger(hours=1),
        args=[supabase_url, supabase_key],
        id="first_recipe_nudge",
        name="First recipe nudge (24h after signup)",
        replace_existing=True
    )

    # Weekly credits refresh - Monday at 12:00 UTC (lunchtime)
    scheduler.add_job(
        process_weekly_credits_refresh,
        trigger=CronTrigger(day_of_week="mon", hour=12, minute=0, timezone="UTC"),
        args=[supabase_url, supabase_key],
        id="weekly_credits_refresh",
        name="Weekly credits refresh notification",
        replace_existing=True
    )

    # Cook tonight - every hour (will check user's preferred time)
    scheduler.add_job(
        process_cook_tonight,
        trigger=IntervalTrigger(hours=1),
        args=[supabase_url, supabase_key],
        id="cook_tonight",
        name="Cook tonight suggestions",
        replace_existing=True
    )

    # Miss you - daily at 18:00 UTC
    scheduler.add_job(
        process_miss_you,
        trigger=CronTrigger(hour=18, minute=0, timezone="UTC"),
        args=[supabase_url, supabase_key],
        id="miss_you",
        name="Re-engagement notification (7+ days inactive)",
        replace_existing=True
    )

    scheduler.start()
    logger.info(
        "Started notification scheduler with jobs: "
        "first_recipe_nudge (hourly), weekly_credits_refresh (Mon 12:00 UTC), "
        "cook_tonight (hourly), miss_you (daily 18:00 UTC)"
    )

    return scheduler
