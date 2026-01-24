"""
Push Token Repository

Handles CRUD operations for push notification tokens.
"""
from typing import Optional, List, Dict, Any
from supabase import Client
from app.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)


class PushTokenRepository(BaseRepository):
    """Repository for managing push notification tokens"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "push_tokens")

    async def register_token(
        self,
        user_id: str,
        expo_push_token: str,
        platform: str,
        device_id: Optional[str] = None,
        app_version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Register or update a push token.

        If the token already exists, updates the associated metadata.
        """
        try:
            data = {
                "user_id": user_id,
                "expo_push_token": expo_push_token,
                "platform": platform,
                "device_id": device_id,
                "app_version": app_version,
                "is_active": True,
                "last_used_at": "now()"
            }

            response = self.supabase.table(self.table_name).upsert(
                data,
                on_conflict="expo_push_token"
            ).execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error registering push token: {str(e)}")
            raise

    async def get_active_tokens_for_user(self, user_id: str) -> List[str]:
        """Get all active push tokens for a user"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("expo_push_token")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .execute()

            return [t["expo_push_token"] for t in (response.data or [])]
        except Exception as e:
            logger.error(f"Error fetching push tokens for user {user_id}: {str(e)}")
            raise

    async def get_all_active_tokens_for_users(self, user_ids: List[str]) -> Dict[str, List[str]]:
        """Get all active push tokens for multiple users"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("user_id, expo_push_token")\
                .in_("user_id", user_ids)\
                .eq("is_active", True)\
                .execute()

            # Group tokens by user_id
            result: Dict[str, List[str]] = {}
            for token_data in (response.data or []):
                uid = token_data["user_id"]
                if uid not in result:
                    result[uid] = []
                result[uid].append(token_data["expo_push_token"])

            return result
        except Exception as e:
            logger.error(f"Error fetching push tokens for users: {str(e)}")
            raise

    async def deactivate_token(self, expo_push_token: str) -> None:
        """Mark a token as inactive (e.g., device unregistered)"""
        try:
            self.supabase.table(self.table_name).update({
                "is_active": False
            }).eq("expo_push_token", expo_push_token).execute()

            logger.info(f"Deactivated push token: {expo_push_token[:30]}...")
        except Exception as e:
            logger.error(f"Error deactivating push token: {str(e)}")
            raise

    async def deactivate_tokens_for_user(self, user_id: str) -> None:
        """Deactivate all tokens for a user (e.g., on logout)"""
        try:
            self.supabase.table(self.table_name).update({
                "is_active": False
            }).eq("user_id", user_id).execute()

            logger.info(f"Deactivated all push tokens for user {user_id}")
        except Exception as e:
            logger.error(f"Error deactivating tokens for user {user_id}: {str(e)}")
            raise

    async def delete_token(self, expo_push_token: str) -> bool:
        """Permanently delete a push token"""
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("expo_push_token", expo_push_token)\
                .execute()

            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting push token: {str(e)}")
            raise

    async def update_last_used(self, expo_push_token: str) -> None:
        """Update the last_used_at timestamp for a token"""
        try:
            self.supabase.table(self.table_name).update({
                "last_used_at": "now()"
            }).eq("expo_push_token", expo_push_token).execute()
        except Exception as e:
            logger.error(f"Error updating token last_used_at: {str(e)}")
            # Don't raise - this is not critical
