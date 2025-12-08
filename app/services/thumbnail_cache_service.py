"""
Thumbnail Cache Service

Handles downloading, caching, and refreshing video thumbnails in Supabase Storage.
This prevents broken image URLs when platforms (TikTok, Instagram, YouTube) change
their thumbnail URLs over time.
"""
import logging
import asyncio
from typing import Optional, Dict, Any

import httpx
import yt_dlp

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "recipe-images"
THUMBNAIL_TIMEOUT = 15.0  # seconds


class ThumbnailCacheService:
    """Service for caching video thumbnails in Supabase Storage."""

    def __init__(self, supabase_client):
        """Initialize with Supabase client for storage operations.

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client

    async def cache_thumbnail(
        self,
        thumbnail_url: str,
        recipe_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        Download thumbnail from platform URL and upload to Supabase Storage.

        Args:
            thumbnail_url: Platform thumbnail URL (from yt-dlp)
            recipe_id: Recipe ID for storage path
            user_id: User ID for storage path

        Returns:
            Supabase public URL, or None if failed
        """
        try:
            # Download thumbnail from platform
            async with httpx.AsyncClient(timeout=THUMBNAIL_TIMEOUT) as client:
                response = await client.get(thumbnail_url)

                if response.status_code != 200:
                    logger.warning(
                        f"Failed to download thumbnail: HTTP {response.status_code} "
                        f"from {thumbnail_url[:100]}..."
                    )
                    return None

                image_data = response.content

                if len(image_data) < 1000:  # Less than 1KB is likely an error
                    logger.warning(f"Thumbnail too small ({len(image_data)} bytes), skipping")
                    return None

                logger.info(f"Downloaded thumbnail: {len(image_data)} bytes")

            # Generate storage path
            file_name = f"{recipe_id}-thumbnail.jpg"
            storage_path = f"{user_id}/{file_name}"

            # Upload to Supabase Storage
            self.supabase.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=image_data,
                file_options={
                    "content-type": "image/jpeg",
                    "cache-control": "3600",
                    "upsert": "true"  # Overwrite if exists (for refresh)
                }
            )

            # Get public URL
            public_url = self.supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
            logger.info(f"Thumbnail cached to Supabase: {storage_path}")

            return public_url

        except httpx.TimeoutException:
            logger.warning(f"Timeout downloading thumbnail from {thumbnail_url[:100]}...")
            return None
        except Exception as e:
            logger.error(f"Failed to cache thumbnail: {e}", exc_info=True)
            return None

    async def fetch_fresh_metadata(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch fresh metadata from yt-dlp without downloading the video.

        Used to check if thumbnail has changed since last extraction.

        Args:
            video_url: Original video URL

        Returns:
            Dict with thumbnail URL and other metadata, or None if failed
        """
        def _sync_fetch():
            """Synchronous metadata fetch - runs in thread pool"""
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'extract_flat': False,  # Get full metadata
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return {
                    "thumbnail": info.get("thumbnail"),
                    "title": info.get("title"),
                    "id": info.get("id"),
                }

        try:
            return await asyncio.to_thread(_sync_fetch)
        except Exception as e:
            logger.warning(f"Failed to fetch fresh metadata for {video_url[:100]}...: {e}")
            return None
