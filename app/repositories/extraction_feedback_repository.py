"""
Extraction feedback repository for database operations
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ExtractionFeedbackRepository(BaseRepository):
    """Repository for extraction feedback operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "extraction_feedback")

    async def create_feedback(
        self,
        recipe_id: str,
        user_id: str,
        category: str,
        description: Optional[str] = None,
        extraction_job_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create new extraction feedback.

        Args:
            recipe_id: ID of the recipe with extraction issues
            user_id: ID of the user submitting feedback
            category: Feedback category (from ExtractionFeedbackCategory enum)
            description: Optional additional details
            extraction_job_id: Optional link to extraction job for debugging

        Returns:
            Created feedback or None if failed
        """
        try:
            data = {
                "recipe_id": recipe_id,
                "user_id": user_id,
                "category": category,
            }
            if description:
                data["description"] = description
            if extraction_job_id:
                data["extraction_job_id"] = extraction_job_id

            return await self.create(data)
        except Exception as e:
            logger.error(f"Error creating extraction feedback: {str(e)}")
            raise

    async def get_user_feedback(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get feedback submitted by a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of feedback items to return
            offset: Number of items to skip

        Returns:
            List of feedback with recipe info
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, recipes(id, title, image_url)")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user feedback: {str(e)}")
            raise

    async def get_feedback_with_details(
        self,
        feedback_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get feedback with full recipe and user details.

        Args:
            feedback_id: ID of the feedback

        Returns:
            Feedback with nested recipe and user info
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    recipes(
                        id, title, description, image_url,
                        created_by, source_url, source_type,
                        ingredients, instructions
                    ),
                    user:user_id(id, name, avatar_url),
                    resolved_by_user:resolved_by(id, name, avatar_url),
                    extraction_jobs(id, status, error_message)
                """)\
                .eq("id", feedback_id)\
                .single()\
                .execute()

            return response.data
        except Exception as e:
            logger.error(f"Error fetching feedback details: {str(e)}")
            raise

    async def get_pending_feedback(
        self,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending feedback for admin review.

        Args:
            limit: Maximum number of feedback items to return
            offset: Number of items to skip
            category: Optional filter by category

        Returns:
            List of pending feedback with recipe info
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    recipes(id, title, image_url, source_type),
                    user:user_id(id, name, avatar_url)
                """)\
                .eq("status", "pending")\
                .order("created_at", desc=True)

            if category:
                query = query.eq("category", category)

            response = query.limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching pending feedback: {str(e)}")
            raise

    async def get_feedback_for_recipe(
        self,
        recipe_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all feedback for a specific recipe.

        Args:
            recipe_id: ID of the recipe
            limit: Maximum number of feedback items to return

        Returns:
            List of feedback for the recipe
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, user:user_id(id, name, avatar_url)")\
                .eq("recipe_id", recipe_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching feedback for recipe: {str(e)}")
            raise

    async def resolve_feedback(
        self,
        feedback_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None,
        was_helpful: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Mark feedback as resolved.

        Args:
            feedback_id: ID of the feedback
            resolved_by: ID of the moderator resolving
            resolution_notes: Optional notes about resolution
            was_helpful: Whether the feedback was helpful for improvement

        Returns:
            Updated feedback or None if failed
        """
        try:
            data = {
                "status": "resolved",
                "resolved_by": resolved_by,
                "resolved_at": "now()"
            }

            if resolution_notes:
                data["resolution_notes"] = resolution_notes
            if was_helpful is not None:
                data["was_helpful"] = was_helpful

            return await self.update(feedback_id, data)
        except Exception as e:
            logger.error(f"Error resolving feedback: {str(e)}")
            raise

    async def check_existing_feedback(
        self,
        recipe_id: str,
        user_id: str,
        category: str
    ) -> bool:
        """
        Check if user has already submitted feedback for this category.

        Args:
            recipe_id: ID of the recipe
            user_id: ID of the user
            category: Feedback category

        Returns:
            True if feedback exists, False otherwise
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("recipe_id", recipe_id)\
                .eq("user_id", user_id)\
                .eq("category", category)\
                .execute()

            return len(response.data or []) > 0
        except Exception as e:
            logger.error(f"Error checking existing feedback: {str(e)}")
            raise

    async def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Get overall feedback statistics for admin dashboard.

        Returns:
            Dictionary with feedback counts by status and category
        """
        try:
            # Get counts by status
            pending = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("status", "pending")\
                .execute()

            resolved = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("status", "resolved")\
                .execute()

            helpful = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("was_helpful", True)\
                .execute()

            # Get counts by category (for pending only)
            categories = {}
            for category in ["wrong_ingredients", "missing_steps", "incorrect_steps",
                           "bad_formatting", "wrong_measurements", "wrong_servings",
                           "ai_hallucination", "wrong_title", "wrong_image", "other"]:
                count_response = self.supabase.table(self.table_name)\
                    .select("id", count="exact")\
                    .eq("status", "pending")\
                    .eq("category", category)\
                    .execute()
                categories[category] = count_response.count or 0

            return {
                "by_status": {
                    "pending": pending.count or 0,
                    "resolved": resolved.count or 0,
                    "helpful": helpful.count or 0
                },
                "pending_by_category": categories
            }
        except Exception as e:
            logger.error(f"Error getting feedback statistics: {str(e)}")
            raise
