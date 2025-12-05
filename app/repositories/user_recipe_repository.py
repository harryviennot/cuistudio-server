"""
User recipe data repository
"""
from typing import Optional, Dict, Any, List
from supabase import Client
import logging
from datetime import datetime, timezone

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRecipeRepository(BaseRepository):
    """Repository for user-specific recipe data"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "user_recipe_data")

    async def get_by_user_and_recipe(
        self,
        user_id: str,
        recipe_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user data for a specific recipe"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("recipe_id", recipe_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching user recipe data: {str(e)}")
            raise

    async def get_user_data_for_recipes(
        self,
        user_id: str,
        recipe_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Batch fetch user data for multiple recipes in a single query.
        Returns a dict mapping recipe_id -> user_data

        This eliminates N+1 query problem when loading recipe lists.
        """
        try:
            if not recipe_ids:
                return {}

            response = self.supabase.table(self.table_name)\
                .select("recipe_id, rating, is_favorite")\
                .eq("user_id", user_id)\
                .in_("recipe_id", recipe_ids)\
                .execute()

            # Create map of recipe_id -> user_data for O(1) lookups
            return {row["recipe_id"]: row for row in (response.data or [])}
        except Exception as e:
            logger.error(f"Error batch fetching user recipe data: {str(e)}")
            raise

    async def upsert_user_data(
        self,
        user_id: str,
        recipe_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update user recipe data"""
        try:
            # Add user_id and recipe_id to data
            full_data = {
                "user_id": user_id,
                "recipe_id": recipe_id,
                **data
            }

            response = self.supabase.table(self.table_name)\
                .upsert(full_data, on_conflict="user_id,recipe_id")\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error upserting user recipe data: {str(e)}")
            raise

    async def get_user_favorites(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> list[Dict[str, Any]]:
        """Get user's favorite recipes"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, recipes(*)")\
                .eq("user_id", user_id)\
                .eq("is_favorite", True)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user favorites: {str(e)}")
            raise

    async def increment_cooked_count(
        self,
        user_id: str,
        recipe_id: str
    ) -> Dict[str, Any]:
        """
        Increment the times cooked counter and record cooking event.

        This performs two operations:
        1. Updates user_recipe_data.times_cooked (personal count)
        2. Inserts a cooking event for time-based analytics

        The recipes.total_times_cooked is updated automatically by database trigger.
        """
        try:
            # Get current data
            current = await self.get_by_user_and_recipe(user_id, recipe_id)

            times_cooked = (current["times_cooked"] if current else 0) + 1
            now = datetime.now(timezone.utc).isoformat()

            # Insert cooking event for time-based analytics
            # This enables queries like "most cooked this week"
            self.supabase.table("recipe_cooking_events")\
                .insert({
                    "user_id": user_id,
                    "recipe_id": recipe_id,
                    "cooked_at": now
                })\
                .execute()

            # Upsert with incremented count
            return await self.upsert_user_data(
                user_id,
                recipe_id,
                {
                    "times_cooked": times_cooked,
                    "last_cooked_at": now
                }
            )
        except Exception as e:
            logger.error(f"Error incrementing cooked count: {str(e)}")
            raise

    async def get_previous_rating(
        self,
        user_id: str,
        recipe_id: str
    ) -> Optional[float]:
        """
        Get user's previous rating for a recipe (supports half-stars).

        Returns:
            Previous rating (0.5-5.0 in 0.5 increments) or None if no previous rating exists
        """
        try:
            user_data = await self.get_by_user_and_recipe(user_id, recipe_id)
            return user_data.get("rating") if user_data else None
        except Exception as e:
            logger.error(f"Error fetching previous rating: {str(e)}")
            raise

    # =============================================
    # Collection-related methods (virtual collections)
    # =============================================

    async def get_user_extracted_recipes(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recipes that the user has extracted.

        Returns user_recipe_data records with full recipe details
        where was_extracted = true.
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    recipes!inner(
                        id, title, description, image_url,
                        servings, difficulty, tags,
                        source_type, is_public, created_at
                    )
                """)\
                .eq("user_id", user_id)\
                .eq("was_extracted", True)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user extracted recipes: {str(e)}")
            raise

    async def count_user_extracted_recipes(self, user_id: str) -> int:
        """Count recipes that the user has extracted."""
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("was_extracted", True)\
                .execute()

            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting user extracted recipes: {str(e)}")
            raise

    async def count_user_favorites(self, user_id: str) -> int:
        """Count recipes that the user has favorited."""
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("is_favorite", True)\
                .execute()

            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting user favorites: {str(e)}")
            raise

    async def mark_as_extracted(
        self,
        user_id: str,
        recipe_id: str
    ) -> Dict[str, Any]:
        """
        Mark a recipe as extracted by this user.

        This is used when:
        1. User extracts a new recipe
        2. User extracts a duplicate (recipe already exists)

        Uses upsert to handle both new and existing records.
        """
        try:
            return await self.upsert_user_data(
                user_id,
                recipe_id,
                {"was_extracted": True}
            )
        except Exception as e:
            logger.error(f"Error marking recipe as extracted: {str(e)}")
            raise

    async def set_favorite(
        self,
        user_id: str,
        recipe_id: str,
        is_favorite: bool
    ) -> Dict[str, Any]:
        """
        Set the favorite status for a recipe.

        Args:
            user_id: User ID
            recipe_id: Recipe ID
            is_favorite: True to favorite, False to unfavorite
        """
        try:
            return await self.upsert_user_data(
                user_id,
                recipe_id,
                {"is_favorite": is_favorite}
            )
        except Exception as e:
            logger.error(f"Error setting favorite status: {str(e)}")
            raise
