"""
Repository for collection recipes (many-to-many relationship)
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CollectionRecipeRepository(BaseRepository):
    """Repository for collection recipe operations (many-to-many)"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "collection_recipes")

    async def add_recipe_to_collection(
        self,
        collection_id: str,
        recipe_id: str,
        sort_order: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Add a recipe to a collection.

        Args:
            collection_id: Collection ID
            recipe_id: Recipe ID to add
            sort_order: Display order within collection

        Returns:
            Created record or None if already exists
        """
        try:
            data = {
                "collection_id": collection_id,
                "recipe_id": recipe_id,
                "sort_order": sort_order
            }
            response = self.supabase.table(self.table_name).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            # Check if it's a unique constraint violation
            if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                logger.info(f"Recipe {recipe_id} already in collection {collection_id}")
                return None
            logger.error(f"Error adding recipe to collection: {str(e)}")
            raise

    async def remove_recipe_from_collection(
        self,
        collection_id: str,
        recipe_id: str
    ) -> bool:
        """
        Remove a recipe from a collection.

        Args:
            collection_id: Collection ID
            recipe_id: Recipe ID to remove

        Returns:
            True if removed, False if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("collection_id", collection_id)\
                .eq("recipe_id", recipe_id)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error removing recipe from collection: {str(e)}")
            raise

    async def is_recipe_in_collection(
        self,
        collection_id: str,
        recipe_id: str
    ) -> bool:
        """
        Check if a recipe is in a collection.

        Args:
            collection_id: Collection ID
            recipe_id: Recipe ID to check

        Returns:
            True if in collection, False otherwise
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("collection_id", collection_id)\
                .eq("recipe_id", recipe_id)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error checking collection: {str(e)}")
            raise

    async def get_collection_recipes(
        self,
        collection_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all recipes in a collection with recipe details.

        Args:
            collection_id: Collection ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of recipes with collection metadata
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    id, sort_order, created_at,
                    recipe:recipes(
                        id, title, description, image_url,
                        servings, difficulty, tags, categories,
                        prep_time_minutes, cook_time_minutes, total_time_minutes,
                        source_type, created_by, is_public, is_draft, fork_count,
                        average_rating, rating_count, total_times_cooked,
                        created_at
                    )
                """)\
                .eq("collection_id", collection_id)\
                .order("sort_order")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching collection recipes: {str(e)}")
            raise

    async def count_collection_recipes(self, collection_id: str) -> int:
        """
        Count recipes in a collection.

        Args:
            collection_id: Collection ID

        Returns:
            Number of recipes in collection
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("collection_id", collection_id)\
                .execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting collection recipes: {str(e)}")
            raise

    async def get_recipe_collections(self, recipe_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all collections that contain a specific recipe for a user.

        Args:
            recipe_id: Recipe ID
            user_id: User ID

        Returns:
            List of collections containing the recipe
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("""
                    id, sort_order, created_at,
                    collection:user_collections(
                        id, name, slug, is_system, user_id
                    )
                """)\
                .eq("recipe_id", recipe_id)\
                .execute()

            # Filter to only user's collections
            result = []
            for item in response.data or []:
                collection = item.get("collection", {})
                if collection.get("user_id") == user_id:
                    result.append(item)
            return result
        except Exception as e:
            logger.error(f"Error fetching recipe collections: {str(e)}")
            raise

    async def update_sort_order(
        self,
        collection_id: str,
        recipe_id: str,
        sort_order: int
    ) -> Optional[Dict[str, Any]]:
        """
        Update the sort order of a recipe within a collection.

        Args:
            collection_id: Collection ID
            recipe_id: Recipe ID
            sort_order: New sort order

        Returns:
            Updated record or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update({"sort_order": sort_order})\
                .eq("collection_id", collection_id)\
                .eq("recipe_id", recipe_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating sort order: {str(e)}")
            raise

    async def remove_recipe_from_all_user_collections(
        self,
        recipe_id: str,
        user_id: str
    ) -> int:
        """
        Remove a recipe from all of a user's collections.

        Args:
            recipe_id: Recipe ID
            user_id: User ID

        Returns:
            Number of collections recipe was removed from
        """
        try:
            # First get all collection IDs for this user
            collections_response = self.supabase.table("user_collections")\
                .select("id")\
                .eq("user_id", user_id)\
                .execute()

            collection_ids = [c["id"] for c in collections_response.data or []]
            if not collection_ids:
                return 0

            # Delete from all user's collections
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("recipe_id", recipe_id)\
                .in_("collection_id", collection_ids)\
                .execute()

            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Error removing recipe from all collections: {str(e)}")
            raise
