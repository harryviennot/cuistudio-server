"""
Content report repository for database operations
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ContentReportRepository(BaseRepository):
    """Repository for content report operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "content_reports")

    async def create_report(
        self,
        recipe_id: str,
        reporter_user_id: str,
        reason: str,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new content report.

        Args:
            recipe_id: ID of the recipe being reported
            reporter_user_id: ID of the user submitting the report
            reason: Report reason (from ContentReportReason enum)
            description: Optional additional details

        Returns:
            Created report or None if failed
        """
        try:
            data = {
                "recipe_id": recipe_id,
                "reporter_user_id": reporter_user_id,
                "reason": reason,
            }
            if description:
                data["description"] = description

            return await self.create(data)
        except Exception as e:
            logger.error(f"Error creating content report: {str(e)}")
            raise

    async def get_user_reports(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get reports submitted by a user.

        Args:
            user_id: ID of the reporting user
            limit: Maximum number of reports to return
            offset: Number of reports to skip

        Returns:
            List of reports with recipe info
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, recipes(id, title, image_url)")\
                .eq("reporter_user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user reports: {str(e)}")
            raise

    async def get_report_with_details(
        self,
        report_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a report with full recipe and reporter details.

        Args:
            report_id: ID of the report

        Returns:
            Report with nested recipe and user info
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    recipes(
                        id, title, description, image_url,
                        created_by, is_public, source_url,
                        ingredients, instructions
                    ),
                    reporter:reporter_user_id(id, name, avatar_url),
                    resolved_by_user:resolved_by(id, name, avatar_url)
                """)\
                .eq("id", report_id)\
                .single()\
                .execute()

            return response.data
        except Exception as e:
            logger.error(f"Error fetching report details: {str(e)}")
            raise

    async def get_pending_reports(
        self,
        limit: int = 50,
        offset: int = 0,
        reason: Optional[str] = None,
        min_priority: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending reports for admin review, sorted by priority.

        Args:
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            reason: Optional filter by reason
            min_priority: Optional minimum priority threshold

        Returns:
            List of pending reports with recipe info
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    recipes(id, title, image_url, created_by),
                    reporter:reporter_user_id(id, name, avatar_url)
                """)\
                .eq("status", "pending")\
                .order("priority", desc=True)\
                .order("created_at", desc=True)

            if reason:
                query = query.eq("reason", reason)

            if min_priority is not None:
                query = query.gte("priority", min_priority)

            response = query.limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching pending reports: {str(e)}")
            raise

    async def get_reports_for_recipe(
        self,
        recipe_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all reports for a specific recipe.

        Args:
            recipe_id: ID of the recipe
            limit: Maximum number of reports to return

        Returns:
            List of reports for the recipe
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, reporter:reporter_user_id(id, name, avatar_url)")\
                .eq("recipe_id", recipe_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching reports for recipe: {str(e)}")
            raise

    async def update_status(
        self,
        report_id: str,
        status: str,
        resolved_by: Optional[str] = None,
        resolution_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update report status.

        Args:
            report_id: ID of the report
            status: New status (from ReportStatus enum)
            resolved_by: ID of the moderator resolving (if resolved)
            resolution_notes: Optional notes about resolution

        Returns:
            Updated report or None if failed
        """
        try:
            data = {"status": status}

            if status == "resolved" and resolved_by:
                data["resolved_by"] = resolved_by
                data["resolved_at"] = "now()"

            if resolution_notes:
                data["resolution_notes"] = resolution_notes

            return await self.update(report_id, data)
        except Exception as e:
            logger.error(f"Error updating report status: {str(e)}")
            raise

    async def check_existing_report(
        self,
        recipe_id: str,
        reporter_user_id: str
    ) -> bool:
        """
        Check if user has already reported this recipe.

        Args:
            recipe_id: ID of the recipe
            reporter_user_id: ID of the reporter

        Returns:
            True if a report exists, False otherwise
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("recipe_id", recipe_id)\
                .eq("reporter_user_id", reporter_user_id)\
                .execute()

            return len(response.data or []) > 0
        except Exception as e:
            logger.error(f"Error checking existing report: {str(e)}")
            raise

    async def count_user_recent_reports(
        self,
        user_id: str,
        hours: int = 24
    ) -> int:
        """
        Count reports submitted by user in the last N hours.

        Args:
            user_id: ID of the user
            hours: Time window in hours

        Returns:
            Number of reports in the time window
        """
        try:
            # Use RPC to call the rate limit check function
            self.supabase.rpc(
                'check_report_rate_limit',
                {'p_user_id': user_id}
            ).execute()

            # Function returns true if under limit, false if at limit
            # We need to return the count, so let's query directly
            from datetime import datetime, timedelta
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            count_response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("reporter_user_id", user_id)\
                .gte("created_at", cutoff)\
                .execute()

            return count_response.count or 0
        except Exception as e:
            logger.error(f"Error counting user recent reports: {str(e)}")
            raise

    async def get_report_statistics(self) -> Dict[str, Any]:
        """
        Get overall report statistics for admin dashboard.

        Returns:
            Dictionary with report counts by status and reason
        """
        try:
            # Get counts by status
            pending = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("status", "pending")\
                .execute()

            in_review = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("status", "in_review")\
                .execute()

            resolved = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("status", "resolved")\
                .execute()

            # Get counts by reason (for pending only)
            reasons = {}
            for reason in ["inappropriate_content", "hate_speech", "copyright_violation",
                          "spam_advertising", "misinformation", "other"]:
                count_response = self.supabase.table(self.table_name)\
                    .select("id", count="exact")\
                    .eq("status", "pending")\
                    .eq("reason", reason)\
                    .execute()
                reasons[reason] = count_response.count or 0

            return {
                "by_status": {
                    "pending": pending.count or 0,
                    "in_review": in_review.count or 0,
                    "resolved": resolved.count or 0
                },
                "pending_by_reason": reasons
            }
        except Exception as e:
            logger.error(f"Error getting report statistics: {str(e)}")
            raise
