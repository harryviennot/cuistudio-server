"""
Moderation action repository for audit logging
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ModerationActionRepository(BaseRepository):
    """Repository for moderation action audit log operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "moderation_actions")

    async def log_action(
        self,
        moderator_id: str,
        action_type: str,
        reason: str,
        target_user_id: Optional[str] = None,
        target_recipe_id: Optional[str] = None,
        content_report_id: Optional[str] = None,
        extraction_feedback_id: Optional[str] = None,
        notes: Optional[str] = None,
        duration_days: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Log a moderation action for audit purposes.

        Args:
            moderator_id: ID of the moderator performing the action
            action_type: Type of action (from ModerationActionType enum)
            reason: Reason for the action
            target_user_id: ID of the user being moderated (if applicable)
            target_recipe_id: ID of the recipe being moderated (if applicable)
            content_report_id: ID of the related content report (if applicable)
            extraction_feedback_id: ID of the related feedback (if applicable)
            notes: Optional internal notes
            duration_days: Duration in days for suspensions

        Returns:
            Created action record or None if failed
        """
        try:
            data = {
                "moderator_id": moderator_id,
                "action_type": action_type,
                "reason": reason,
            }

            if target_user_id:
                data["target_user_id"] = target_user_id
            if target_recipe_id:
                data["target_recipe_id"] = target_recipe_id
            if content_report_id:
                data["content_report_id"] = content_report_id
            if extraction_feedback_id:
                data["extraction_feedback_id"] = extraction_feedback_id
            if notes:
                data["notes"] = notes
            if duration_days is not None:
                data["duration_days"] = duration_days

            return await self.create(data)
        except Exception as e:
            logger.error(f"Error logging moderation action: {str(e)}")
            raise

    async def get_actions_for_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get moderation actions targeting a specific user.

        Args:
            user_id: ID of the target user
            limit: Maximum number of actions to return
            offset: Number of actions to skip

        Returns:
            List of moderation actions with moderator info
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, moderator:moderator_id(id, name, avatar_url)")\
                .eq("target_user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching actions for user: {str(e)}")
            raise

    async def get_actions_for_recipe(
        self,
        recipe_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get moderation actions targeting a specific recipe.

        Args:
            recipe_id: ID of the target recipe
            limit: Maximum number of actions to return
            offset: Number of actions to skip

        Returns:
            List of moderation actions with moderator info
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, moderator:moderator_id(id, name, avatar_url)")\
                .eq("target_recipe_id", recipe_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching actions for recipe: {str(e)}")
            raise

    async def get_actions_by_moderator(
        self,
        moderator_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get moderation actions performed by a specific moderator.

        Args:
            moderator_id: ID of the moderator
            limit: Maximum number of actions to return
            offset: Number of actions to skip

        Returns:
            List of moderation actions
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    target_user:target_user_id(id, name, avatar_url),
                    target_recipe:target_recipe_id(id, title)
                """)\
                .eq("moderator_id", moderator_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching actions by moderator: {str(e)}")
            raise

    async def get_recent_actions(
        self,
        limit: int = 100,
        offset: int = 0,
        action_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent moderation actions.

        Args:
            limit: Maximum number of actions to return
            offset: Number of actions to skip
            action_type: Optional filter by action type

        Returns:
            List of recent moderation actions
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    moderator:moderator_id(id, name, avatar_url),
                    target_user:target_user_id(id, name, avatar_url),
                    target_recipe:target_recipe_id(id, title)
                """)\
                .order("created_at", desc=True)

            if action_type:
                query = query.eq("action_type", action_type)

            response = query.limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching recent actions: {str(e)}")
            raise

    async def get_action_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get moderation action statistics for a time period.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with action counts by type
        """
        try:
            from datetime import datetime, timedelta
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

            stats = {}
            action_types = [
                "dismiss_report", "hide_recipe", "unhide_recipe",
                "warn_user", "suspend_user", "unsuspend_user",
                "ban_user", "unban_user", "resolve_feedback"
            ]

            for action_type in action_types:
                response = self.supabase.table(self.table_name)\
                    .select("id", count="exact")\
                    .eq("action_type", action_type)\
                    .gte("created_at", cutoff)\
                    .execute()
                stats[action_type] = response.count or 0

            # Total actions
            total_response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .gte("created_at", cutoff)\
                .execute()

            return {
                "by_type": stats,
                "total": total_response.count or 0,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error getting action statistics: {str(e)}")
            raise


class UserWarningRepository(BaseRepository):
    """Repository for user warning operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "user_warnings")

    async def create_warning(
        self,
        user_id: str,
        issued_by: str,
        reason: str,
        content_report_id: Optional[str] = None,
        recipe_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new warning for a user.

        Args:
            user_id: ID of the user receiving the warning
            issued_by: ID of the moderator issuing the warning
            reason: Reason for the warning
            content_report_id: ID of the related report (if applicable)
            recipe_id: ID of the related recipe (if applicable)

        Returns:
            Created warning record or None if failed
        """
        try:
            data = {
                "user_id": user_id,
                "issued_by": issued_by,
                "reason": reason,
            }

            if content_report_id:
                data["content_report_id"] = content_report_id
            if recipe_id:
                data["recipe_id"] = recipe_id

            return await self.create(data)
        except Exception as e:
            logger.error(f"Error creating warning: {str(e)}")
            raise

    async def get_user_warnings(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get warnings for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of warnings to return
            offset: Number of warnings to skip

        Returns:
            List of warnings with issuer info
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    issuer:issued_by(id, name, avatar_url),
                    recipes(id, title)
                """)\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user warnings: {str(e)}")
            raise

    async def get_unacknowledged_warnings(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get warnings that the user hasn't acknowledged.

        Args:
            user_id: ID of the user

        Returns:
            List of unacknowledged warnings
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .is_("acknowledged_at", "null")\
                .order("created_at", desc=True)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching unacknowledged warnings: {str(e)}")
            raise

    async def acknowledge_warning(
        self,
        warning_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Mark a warning as acknowledged by the user.

        Args:
            warning_id: ID of the warning
            user_id: ID of the user (for verification)

        Returns:
            Updated warning or None if failed/unauthorized
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update({"acknowledged_at": "now()"})\
                .eq("id", warning_id)\
                .eq("user_id", user_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error acknowledging warning: {str(e)}")
            raise
