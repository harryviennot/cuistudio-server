"""
User recipe data repository
"""
from typing import Optional, Dict, Any, List
from supabase import Client
import logging

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
        """Increment the times cooked counter"""
        try:
            # Get current data
            current = await self.get_by_user_and_recipe(user_id, recipe_id)

            times_cooked = (current["times_cooked"] if current else 0) + 1

            # Upsert with incremented count
            return await self.upsert_user_data(
                user_id,
                recipe_id,
                {
                    "times_cooked": times_cooked,
                    "last_cooked_at": "now()"
                }
            )
        except Exception as e:
            logger.error(f"Error incrementing cooked count: {str(e)}")
            raise
