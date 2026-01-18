"""
Repository for video sources (links recipes to source videos for duplicate detection)
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository
from app.services.video_url_parser import VideoURLParser

logger = logging.getLogger(__name__)


class VideoSourceRepository(BaseRepository):
    """Repository for video source operations (duplicate detection)"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "video_sources")

    async def find_by_video_id(
        self,
        platform: str,
        platform_video_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find a video source by platform and video ID.
        Used for duplicate detection.

        Args:
            platform: Platform name ('tiktok', 'youtube', 'instagram')
            platform_video_id: Video ID on the platform

        Returns:
            Video source record or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("platform", platform)\
                .eq("platform_video_id", platform_video_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error finding video source by ID: {str(e)}")
            raise

    async def find_with_recipe(
        self,
        platform: str,
        platform_video_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find a video source with its associated recipe.
        Used for duplicate detection with full recipe data.

        Args:
            platform: Platform name
            platform_video_id: Video ID on the platform

        Returns:
            Video source with recipe data or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    recipe:recipes(*),
                    creator:video_creators(*)
                """)\
                .eq("platform", platform)\
                .eq("platform_video_id", platform_video_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error finding video source with recipe: {str(e)}")
            raise

    async def check_duplicate(
        self,
        platform: str,
        platform_video_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a video has already been extracted.
        Returns recipe info if found.

        Args:
            platform: Platform name
            platform_video_id: Video ID on the platform

        Returns:
            Dict with recipe_id, is_public, created_by or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    recipe_id,
                    recipe:recipes(id, is_public, created_by, title, image_url)
                """)\
                .eq("platform", platform)\
                .eq("platform_video_id", platform_video_id)\
                .execute()

            if not response.data:
                return None

            data = response.data[0]
            recipe = data.get("recipe", {})
            return {
                "recipe_id": data["recipe_id"],
                "is_public": recipe.get("is_public"),
                "created_by": recipe.get("created_by"),
                "title": recipe.get("title"),
                "image_url": recipe.get("image_url")
            }
        except Exception as e:
            logger.error(f"Error checking video duplicate: {str(e)}")
            raise

    async def create_video_source(
        self,
        platform: str,
        platform_video_id: str,
        recipe_id: str,
        original_url: str,
        canonical_url: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        thumbnail_url: Optional[str] = None,
        view_count: Optional[int] = None,
        like_count: Optional[int] = None,
        upload_date: Optional[str] = None,
        video_creator_id: Optional[str] = None,
        raw_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a video source record linking a recipe to its source video.

        Args:
            platform: Platform name
            platform_video_id: Video ID on the platform
            recipe_id: Associated recipe ID
            original_url: Original URL submitted by user
            canonical_url: Canonical URL from platform
            title: Video title
            description: Video description
            duration_seconds: Video duration
            thumbnail_url: Thumbnail URL
            view_count: View count
            like_count: Like count
            upload_date: Upload date (YYYY-MM-DD format)
            video_creator_id: Associated video creator ID
            raw_metadata: Full yt-dlp metadata for future use

        Returns:
            Created video source record
        """
        try:
            # Convert numeric values to integers (yt-dlp may return floats)
            duration_int = int(duration_seconds) if duration_seconds is not None else None
            view_count_int = int(view_count) if view_count is not None else None
            like_count_int = int(like_count) if like_count is not None else None

            # Clean URL to remove tracking parameters
            clean_original_url = VideoURLParser.clean_url(original_url)

            data = {
                "platform": platform,
                "platform_video_id": platform_video_id,
                "recipe_id": recipe_id,
                "original_url": clean_original_url,
                "canonical_url": canonical_url,
                "title": title,
                "description": description,
                "duration_seconds": duration_int,
                "thumbnail_url": thumbnail_url,
                "view_count": view_count_int,
                "like_count": like_count_int,
                "upload_date": upload_date,
                "video_creator_id": video_creator_id,
                "raw_metadata": raw_metadata
            }
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}

            return await self.create(data)
        except Exception as e:
            logger.error(f"Error creating video source: {str(e)}")
            raise

    async def get_by_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video source for a recipe.

        Args:
            recipe_id: Recipe ID

        Returns:
            Video source record or None if recipe wasn't from a video
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    creator:video_creators(*)
                """)\
                .eq("recipe_id", recipe_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting video source by recipe: {str(e)}")
            raise

    async def get_by_recipe_ids(self, recipe_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch fetch video sources for multiple recipes.
        Eliminates N+1 queries when formatting recipe lists.

        Args:
            recipe_ids: List of recipe IDs to fetch video sources for

        Returns:
            Dict mapping recipe_id -> video_source record
        """
        if not recipe_ids:
            return {}

        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    creator:video_creators(*)
                """)\
                .in_("recipe_id", recipe_ids)\
                .execute()

            return {vs["recipe_id"]: vs for vs in (response.data or [])}
        except Exception as e:
            logger.error(f"Error batch fetching video sources: {str(e)}")
            raise

    async def get_recipes_by_creator(
        self,
        video_creator_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all recipes from a specific video creator.

        Args:
            video_creator_id: Video creator ID
            limit: Maximum results
            offset: Results to skip

        Returns:
            List of video sources with recipe data
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    recipe:recipes(*)
                """)\
                .eq("video_creator_id", video_creator_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting recipes by creator: {str(e)}")
            raise

    async def count_by_creator(self, video_creator_id: str) -> int:
        """
        Count recipes from a specific video creator.

        Args:
            video_creator_id: Video creator ID

        Returns:
            Number of recipes from this creator
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("video_creator_id", video_creator_id)\
                .execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting recipes by creator: {str(e)}")
            raise

    async def get_recent_extractions(
        self,
        platform: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recently extracted videos.

        Args:
            platform: Optional platform filter
            limit: Maximum results
            offset: Results to skip

        Returns:
            List of recent video sources with recipe data
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    recipe:recipes(id, title, image_url, is_public),
                    creator:video_creators(platform_username, display_name)
                """)\
                .order("created_at", desc=True)

            if platform:
                query = query.eq("platform", platform)

            response = query.limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting recent extractions: {str(e)}")
            raise
