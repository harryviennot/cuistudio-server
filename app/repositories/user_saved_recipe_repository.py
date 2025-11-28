"""
Repository for user saved recipes (user collections)
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserSavedRecipeRepository(BaseRepository):
    """Repository for user saved recipe operations (user collections)"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "user_saved_recipes")

    async def add_to_collection(
        self,
        user_id: str,
        recipe_id: str,
        source: str = "extracted"
    ) -> Optional[Dict[str, Any]]:
        """
        Add a recipe to user's collection.

        Args:
            user_id: User ID
            recipe_id: Recipe ID to add
            source: How the recipe was added ('extracted', 'saved', 'forked')

        Returns:
            Created record or None if already exists
        """
        try:
            data = {
                "user_id": user_id,
                "recipe_id": recipe_id,
                "source": source
            }
            response = self.supabase.table(self.table_name).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            # Check if it's a unique constraint violation (already in collection)
            if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                logger.info(f"Recipe {recipe_id} already in user {user_id}'s collection")
                return None
            logger.error(f"Error adding recipe to collection: {str(e)}")
            raise

    async def remove_from_collection(self, user_id: str, recipe_id: str) -> bool:
        """
        Remove a recipe from user's collection.

        Args:
            user_id: User ID
            recipe_id: Recipe ID to remove

        Returns:
            True if removed, False if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("user_id", user_id)\
                .eq("recipe_id", recipe_id)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error removing recipe from collection: {str(e)}")
            raise

    async def is_in_collection(self, user_id: str, recipe_id: str) -> bool:
        """
        Check if a recipe is in user's collection.

        Args:
            user_id: User ID
            recipe_id: Recipe ID to check

        Returns:
            True if in collection, False otherwise
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("recipe_id", recipe_id)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking collection: {str(e)}")
            raise

    async def get_user_collection(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        source_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all recipes in user's collection with recipe details.

        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Number of results to skip
            source_filter: Optional filter by source ('extracted', 'saved', 'forked')

        Returns:
            List of saved recipe records with recipe details
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("""
                    id, source, created_at,
                    recipe:recipes(
                        id, title, description, image_url,
                        servings, difficulty, tags, categories,
                        prep_time_minutes, cook_time_minutes, total_time_minutes,
                        source_type, created_by, is_public, fork_count,
                        average_rating, rating_count, total_times_cooked,
                        created_at
                    )
                """)\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)

            if source_filter:
                query = query.eq("source", source_filter)

            response = query.limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user collection: {str(e)}")
            raise

    async def get_collection_recipe_ids(self, user_id: str) -> List[str]:
        """
        Get all recipe IDs in user's collection (for quick lookups).

        Args:
            user_id: User ID

        Returns:
            List of recipe IDs
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("recipe_id")\
                .eq("user_id", user_id)\
                .execute()
            return [item["recipe_id"] for item in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error fetching collection recipe IDs: {str(e)}")
            raise

    async def count_user_collection(self, user_id: str) -> int:
        """
        Count recipes in user's collection.

        Args:
            user_id: User ID

        Returns:
            Number of recipes in collection
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting user collection: {str(e)}")
            raise
