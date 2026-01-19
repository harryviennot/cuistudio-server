"""
User moderation repository for database operations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserModerationRepository(BaseRepository):
    """Repository for user moderation status operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "user_moderation")

    async def get_or_create(self, user_id: str) -> Dict[str, Any]:
        """
        Get user moderation record, creating if it doesn't exist.

        Args:
            user_id: ID of the user

        Returns:
            User moderation record
        """
        try:
            # Try to get existing record
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()

            if response.data:
                return response.data[0]

            # Create new record using database function
            init_response = self.supabase.rpc(
                'initialize_user_moderation',
                {'p_user_id': user_id}
            ).execute()

            return init_response.data
        except Exception as e:
            logger.error(f"Error getting/creating user moderation: {str(e)}")
            raise

    async def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user moderation record by user ID.

        Args:
            user_id: ID of the user

        Returns:
            User moderation record or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .single()\
                .execute()

            return response.data
        except Exception as e:
            # .single() throws if not found - PGRST116 is PostgREST code for "Results contain 0 rows"
            if "PGRST116" in str(e):
                return None
            logger.error(f"Error fetching user moderation: {str(e)}")
            raise

    async def update_status(
        self,
        user_id: str,
        status: str,
        ban_reason: Optional[str] = None,
        suspended_until: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update user moderation status.

        Args:
            user_id: ID of the user
            status: New status (from UserModerationStatus enum)
            ban_reason: Reason for ban (if banning)
            suspended_until: Suspension end time (if suspending)

        Returns:
            Updated record or None if failed
        """
        try:
            # Ensure record exists
            await self.get_or_create(user_id)

            data = {"status": status}

            if ban_reason:
                data["ban_reason"] = ban_reason

            if suspended_until:
                data["suspended_until"] = suspended_until.isoformat()
            elif status in ["good_standing", "warned", "banned"]:
                # Clear suspension time for non-suspended states
                data["suspended_until"] = None

            response = self.supabase.table(self.table_name)\
                .update(data)\
                .eq("user_id", user_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating user moderation status: {str(e)}")
            raise

    async def increment_warning_count(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Increment warning count for a user.

        Args:
            user_id: ID of the user

        Returns:
            Updated record or None if failed
        """
        try:
            # Ensure record exists
            record = await self.get_or_create(user_id)

            new_count = (record.get("warning_count", 0) or 0) + 1

            response = self.supabase.table(self.table_name)\
                .update({
                    "warning_count": new_count,
                    "status": "warned" if new_count > 0 else record["status"]
                })\
                .eq("user_id", user_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error incrementing warning count: {str(e)}")
            raise

    async def increment_report_count(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Increment the count of times this user's content was reported.

        Args:
            user_id: ID of the user whose content was reported

        Returns:
            Updated record or None if failed
        """
        try:
            # Use database function
            self.supabase.rpc(
                'increment_user_report_count',
                {'p_user_id': user_id}
            ).execute()

            return await self.get_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Error incrementing report count: {str(e)}")
            raise

    async def increment_false_report_count(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Increment false report count for a user (reporter submitted false reports).

        Args:
            user_id: ID of the reporting user

        Returns:
            Updated record or None if failed
        """
        try:
            record = await self.get_or_create(user_id)

            new_count = (record.get("false_report_count", 0) or 0) + 1

            response = self.supabase.table(self.table_name)\
                .update({"false_report_count": new_count})\
                .eq("user_id", user_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error incrementing false report count: {str(e)}")
            raise

    async def adjust_reliability_score(
        self,
        user_id: str,
        adjustment: int
    ) -> int:
        """
        Adjust reporter reliability score.

        Args:
            user_id: ID of the reporting user
            adjustment: Points to add (positive) or subtract (negative)

        Returns:
            New reliability score
        """
        try:
            response = self.supabase.rpc(
                'adjust_reporter_reliability',
                {
                    'p_reporter_id': user_id,
                    'p_adjustment': adjustment
                }
            ).execute()

            return response.data
        except Exception as e:
            logger.error(f"Error adjusting reliability score: {str(e)}")
            raise

    async def is_user_banned(self, user_id: str) -> bool:
        """
        Check if a user is currently banned.

        Args:
            user_id: ID of the user

        Returns:
            True if banned, False otherwise
        """
        try:
            record = await self.get_by_user_id(user_id)
            if not record:
                return False

            return record.get("status") == "banned"
        except Exception as e:
            logger.error(f"Error checking ban status: {str(e)}")
            raise

    async def is_user_suspended(self, user_id: str) -> bool:
        """
        Check if a user is currently suspended.

        Args:
            user_id: ID of the user

        Returns:
            True if suspended (and suspension hasn't expired), False otherwise
        """
        try:
            record = await self.get_by_user_id(user_id)
            if not record:
                return False

            if record.get("status") != "suspended":
                return False

            # Check if suspension has expired
            suspended_until = record.get("suspended_until")
            if suspended_until:
                if isinstance(suspended_until, str):
                    suspended_until = datetime.fromisoformat(suspended_until.replace('Z', '+00:00'))

                if datetime.now(suspended_until.tzinfo) > suspended_until:
                    # Suspension expired, update status
                    await self.update_status(user_id, "warned")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error checking suspension status: {str(e)}")
            raise

    async def can_user_report(self, user_id: str) -> bool:
        """
        Check if a user can submit reports (not banned/suspended, has reliability).

        Args:
            user_id: ID of the user

        Returns:
            True if user can report, False otherwise
        """
        try:
            record = await self.get_by_user_id(user_id)
            if not record:
                return True  # New users can report

            # Check status
            status = record.get("status")
            if status in ["banned", "suspended"]:
                return False

            # Check reliability score
            reliability = record.get("reporter_reliability_score", 100)
            if reliability < 20:  # Very low reliability = can't report
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking report ability: {str(e)}")
            raise

    async def get_users_with_status(
        self,
        status: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get users with a specific moderation status.

        Args:
            status: Status to filter by
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of user moderation records with user info
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, users(id, name, avatar_url)")\
                .eq("status", status)\
                .order("updated_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching users with status: {str(e)}")
            raise

    async def get_moderation_statistics(self) -> Dict[str, Any]:
        """
        Get user moderation statistics.

        Returns:
            Dictionary with counts by status
        """
        try:
            stats = {}
            for status in ["good_standing", "warned", "suspended", "banned"]:
                response = self.supabase.table(self.table_name)\
                    .select("id", count="exact")\
                    .eq("status", status)\
                    .execute()
                stats[status] = response.count or 0

            return stats
        except Exception as e:
            logger.error(f"Error getting moderation statistics: {str(e)}")
            raise
