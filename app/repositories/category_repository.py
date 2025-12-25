"""
Category repository for database operations
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CategoryRepository(BaseRepository):
    """Repository for category operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "categories")

    async def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all categories (slug + metadata only, no translations).

        Frontend handles translation via i18n files using the slug as the key.

        Returns:
            List of categories with id, slug, icon, display_order
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id, slug, icon, display_order")\
                .order("display_order")\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            raise

    async def get_all_with_descriptions(self) -> List[Dict[str, Any]]:
        """
        Get all categories with their AI descriptions.
        Used for building AI prompts dynamically.

        Returns:
            List of categories with slug and description
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("slug, description")\
                .order("display_order")\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching categories with descriptions: {str(e)}")
            raise

    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get a category by its slug.

        Args:
            slug: Category slug (e.g., 'soups', 'desserts')

        Returns:
            Category dict or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id, slug, icon, display_order")\
                .eq("slug", slug)\
                .single()\
                .execute()

            return response.data
        except Exception as e:
            # .single() throws if not found, so check if it's a "not found" error
            if "PGRST116" in str(e):  # PostgREST code for "Results contain 0 rows"
                return None
            logger.error(f"Error fetching category by slug {slug}: {str(e)}")
            raise

    async def get_id_by_slug(self, slug: str) -> Optional[str]:
        """
        Get category ID by slug. Optimized for lookups during recipe creation.

        Args:
            slug: Category slug

        Returns:
            Category UUID or None
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("slug", slug)\
                .execute()

            return response.data[0]["id"] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching category ID for slug {slug}: {str(e)}")
            return None

    async def get_recipe_count_by_category(self) -> List[Dict[str, Any]]:
        """
        Get count of recipes per category.
        Useful for displaying category cards with recipe counts.

        Returns:
            List of categories with id, slug, icon, display_order, recipe_count
        """
        try:
            categories = await self.get_all()

            for cat in categories:
                count_response = self.supabase.table("recipes")\
                    .select("id", count="exact")\
                    .eq("category_id", cat["id"])\
                    .eq("is_public", True)\
                    .eq("is_draft", False)\
                    .execute()
                cat["recipe_count"] = count_response.count or 0

            return categories
        except Exception as e:
            logger.error(f"Error fetching recipe counts by category: {str(e)}")
            raise
