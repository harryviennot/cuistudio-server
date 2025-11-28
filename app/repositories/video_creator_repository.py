"""
Repository for video creators (TikTok, YouTube, Instagram content creators)
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class VideoCreatorRepository(BaseRepository):
    """Repository for video creator operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "video_creators")

    async def get_by_platform_id(
        self,
        platform: str,
        platform_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a video creator by platform and platform user ID.

        Args:
            platform: Platform name ('tiktok', 'youtube', 'instagram')
            platform_user_id: User ID on the platform

        Returns:
            Creator record or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("platform", platform)\
                .eq("platform_user_id", platform_user_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching video creator by platform ID: {str(e)}")
            raise

    async def get_by_platform_username(
        self,
        platform: str,
        platform_username: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a video creator by platform and username.

        Note: Usernames can change, so platform_user_id is more reliable.

        Args:
            platform: Platform name
            platform_username: Username on the platform

        Returns:
            Creator record or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("platform", platform)\
                .eq("platform_username", platform_username)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching video creator by username: {str(e)}")
            raise

    async def get_or_create(
        self,
        platform: str,
        platform_user_id: str,
        platform_username: Optional[str] = None,
        display_name: Optional[str] = None,
        profile_url: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get existing creator or create new one.
        Updates metadata if creator exists but info has changed.

        Args:
            platform: Platform name
            platform_user_id: User ID on the platform
            platform_username: Optional username
            display_name: Optional display name
            profile_url: Optional profile URL
            avatar_url: Optional avatar URL

        Returns:
            Creator record (existing or newly created)
        """
        try:
            # Try to find existing creator
            existing = await self.get_by_platform_id(platform, platform_user_id)

            if existing:
                # Update if any info changed
                updates = {}
                if platform_username and platform_username != existing.get("platform_username"):
                    updates["platform_username"] = platform_username
                if display_name and display_name != existing.get("display_name"):
                    updates["display_name"] = display_name
                if profile_url and profile_url != existing.get("profile_url"):
                    updates["profile_url"] = profile_url
                if avatar_url and avatar_url != existing.get("avatar_url"):
                    updates["avatar_url"] = avatar_url

                if updates:
                    updated = await self.update(existing["id"], updates)
                    return updated if updated else existing

                return existing

            # Create new creator
            data = {
                "platform": platform,
                "platform_user_id": platform_user_id,
                "platform_username": platform_username,
                "display_name": display_name,
                "profile_url": profile_url,
                "avatar_url": avatar_url
            }
            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}

            created = await self.create(data)
            return created
        except Exception as e:
            logger.error(f"Error in get_or_create video creator: {str(e)}")
            raise

    async def get_creators_by_user(self, claimed_by_user_id: str) -> List[Dict[str, Any]]:
        """
        Get all video creators claimed by a user.

        Args:
            claimed_by_user_id: Cuistudio user ID

        Returns:
            List of creator records claimed by this user
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("claimed_by_user_id", claimed_by_user_id)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching creators by user: {str(e)}")
            raise

    async def claim_creator(
        self,
        creator_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Claim a video creator profile for a Cuistudio user.

        Args:
            creator_id: Video creator ID
            user_id: Cuistudio user ID claiming ownership

        Returns:
            Updated creator record or None if not found
        """
        try:
            from datetime import datetime, timezone

            response = self.supabase.table(self.table_name)\
                .update({
                    "claimed_by_user_id": user_id,
                    "claimed_at": datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", creator_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error claiming video creator: {str(e)}")
            raise

    async def unclaim_creator(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """
        Remove ownership claim from a video creator profile.

        Args:
            creator_id: Video creator ID

        Returns:
            Updated creator record or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update({
                    "claimed_by_user_id": None,
                    "claimed_at": None
                })\
                .eq("id", creator_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error unclaiming video creator: {str(e)}")
            raise

    async def search_creators(
        self,
        query: str,
        platform: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search video creators by username or display name.

        Args:
            query: Search query
            platform: Optional platform filter
            limit: Maximum results
            offset: Results to skip

        Returns:
            List of matching creators
        """
        try:
            db_query = self.supabase.table(self.table_name)\
                .select("*")\
                .or_(f"platform_username.ilike.%{query}%,display_name.ilike.%{query}%")

            if platform:
                db_query = db_query.eq("platform", platform)

            response = db_query.limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error searching video creators: {str(e)}")
            raise
