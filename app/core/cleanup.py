"""
Cleanup service for temporary files.

Handles automatic cleanup of orphaned temp videos that weren't properly
deleted after extraction (e.g., due to errors or abandoned jobs).
"""
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default settings (can be overridden via config)
TEMP_VIDEO_DIR = "temp/videos"
MAX_AGE_HOURS = 2


def cleanup_old_videos(
    temp_dir: str = TEMP_VIDEO_DIR,
    max_age_hours: int = MAX_AGE_HOURS
) -> dict:
    """
    Delete video files older than max_age_hours.

    Args:
        temp_dir: Directory containing temp videos
        max_age_hours: Maximum age in hours before deletion

    Returns:
        Dict with cleanup statistics
    """
    cutoff = time.time() - (max_age_hours * 3600)
    temp_path = Path(temp_dir)

    stats = {
        "files_deleted": 0,
        "dirs_deleted": 0,
        "bytes_freed": 0,
        "errors": []
    }

    if not temp_path.exists():
        logger.debug(f"Temp video directory does not exist: {temp_dir}")
        return stats

    try:
        for job_dir in temp_path.iterdir():
            if not job_dir.is_dir():
                continue

            # Check each video file in the job directory
            for video_file in list(job_dir.iterdir()):
                try:
                    file_stat = video_file.stat()
                    if file_stat.st_mtime < cutoff:
                        file_size = file_stat.st_size
                        video_file.unlink()
                        stats["files_deleted"] += 1
                        stats["bytes_freed"] += file_size
                        logger.info(f"Deleted old temp video: {video_file}")
                except Exception as e:
                    error_msg = f"Failed to delete {video_file}: {str(e)}"
                    logger.warning(error_msg)
                    stats["errors"].append(error_msg)

            # Remove empty job directories
            try:
                if job_dir.exists() and not any(job_dir.iterdir()):
                    job_dir.rmdir()
                    stats["dirs_deleted"] += 1
                    logger.info(f"Removed empty directory: {job_dir}")
            except Exception as e:
                error_msg = f"Failed to remove directory {job_dir}: {str(e)}"
                logger.warning(error_msg)
                stats["errors"].append(error_msg)

    except Exception as e:
        error_msg = f"Error during cleanup: {str(e)}"
        logger.error(error_msg)
        stats["errors"].append(error_msg)

    if stats["files_deleted"] > 0 or stats["dirs_deleted"] > 0:
        logger.info(
            f"Cleanup complete: {stats['files_deleted']} files, "
            f"{stats['dirs_deleted']} dirs, "
            f"{stats['bytes_freed'] / 1024 / 1024:.2f} MB freed"
        )

    return stats


def start_cleanup_scheduler(
    temp_dir: str = TEMP_VIDEO_DIR,
    max_age_hours: int = MAX_AGE_HOURS,
    interval_hours: int = 1
):
    """
    Start a background scheduler for periodic cleanup.

    Uses APScheduler to run cleanup every interval_hours.

    Args:
        temp_dir: Directory containing temp videos
        max_age_hours: Maximum age in hours before deletion
        interval_hours: How often to run cleanup (in hours)
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger
    except ImportError:
        logger.warning(
            "APScheduler not installed. Temp video cleanup will not run automatically. "
            "Install with: pip install apscheduler"
        )
        return None

    scheduler = AsyncIOScheduler()

    # Add the cleanup job
    scheduler.add_job(
        cleanup_old_videos,
        trigger=IntervalTrigger(hours=interval_hours),
        args=[temp_dir, max_age_hours],
        id="cleanup_temp_videos",
        name="Cleanup old temp videos",
        replace_existing=True
    )

    scheduler.start()
    logger.info(
        f"Started temp video cleanup scheduler: "
        f"runs every {interval_hours}h, deletes files older than {max_age_hours}h"
    )

    return scheduler
