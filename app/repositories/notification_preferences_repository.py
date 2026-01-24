"""
Notification Preferences Repository

Handles CRUD operations for user notification preferences.
"""
from typing import Optional, Dict, Any
from supabase import Client
from app.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)


class NotificationPreferencesRepository(BaseRepository):
    """Repository for managing notification preferences"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "notification_preferences")

    async def get_or_create(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification preferences for a user, creating defaults if needed.
        """
        try:
            # Try to get existing preferences
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()

            if response.data:
                return response.data[0]

            # Create default preferences
            default_prefs = {
                "user_id": user_id,
                "notifications_enabled": True,
                "first_recipe_nudge": True,
                "weekly_credits_refresh": True,
                "referral_activated": True,
                "cook_tonight": True,
                "cooking_streak": True,
                "miss_you": True,
                "timezone": "UTC"
            }

            insert_response = self.supabase.table(self.table_name)\
                .insert(default_prefs)\
                .execute()

            return insert_response.data[0] if insert_response.data else default_prefs
        except Exception as e:
            logger.error(f"Error getting/creating notification preferences: {str(e)}")
            raise

    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update notification preferences for a user.

        Creates the record if it doesn't exist.
        """
        try:
            # Ensure record exists first
            await self.get_or_create(user_id)

            # Filter to only valid preference fields
            valid_fields = {
                "notifications_enabled",
                "first_recipe_nudge",
                "weekly_credits_refresh",
                "referral_activated",
                "cook_tonight",
                "cooking_streak",
                "miss_you",
                "timezone"
            }

            update_data = {k: v for k, v in preferences.items() if k in valid_fields}
            update_data["updated_at"] = "now()"

            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("user_id", user_id)\
                .execute()

            return response.data[0] if response.data else await self.get_or_create(user_id)
        except Exception as e:
            logger.error(f"Error updating notification preferences: {str(e)}")
            raise

    async def is_notification_enabled(
        self,
        user_id: str,
        notification_type: str
    ) -> bool:
        """
        Check if a specific notification type is enabled for a user.

        Returns True if:
        - Master toggle is enabled AND
        - Specific notification type is enabled (or doesn't exist in prefs)
        """
        try:
            prefs = await self.get_or_create(user_id)

            # Check master toggle first
            if not prefs.get("notifications_enabled", True):
                return False

            # Check specific notification type
            return prefs.get(notification_type, True)
        except Exception as e:
            logger.error(f"Error checking notification preference: {str(e)}")
            # Default to enabled on error to avoid silently failing
            return True

    async def get_users_with_preference_enabled(
        self,
        notification_type: str,
        user_ids: Optional[list] = None
    ) -> list:
        """
        Get list of user IDs that have a specific notification type enabled.

        If user_ids is provided, filters to only those users.
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("user_id")\
                .eq("notifications_enabled", True)\
                .eq(notification_type, True)

            if user_ids:
                query = query.in_("user_id", user_ids)

            response = query.execute()

            return [p["user_id"] for p in (response.data or [])]
        except Exception as e:
            logger.error(f"Error getting users with preference enabled: {str(e)}")
            raise
