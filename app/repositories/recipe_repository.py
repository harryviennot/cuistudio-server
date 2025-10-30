"""
Recipe repository for database operations
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class RecipeRepository(BaseRepository):
    """Repository for recipe operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "recipes")

    async def get_with_contributors(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get recipe with contributor information"""
        try:
            # Get recipe
            recipe = await self.get_by_id(recipe_id)
            if not recipe:
                return None

            # Get contributors
            contributors_response = self.supabase.table("recipe_contributors")\
                .select("*")\
                .eq("recipe_id", recipe_id)\
                .order("order")\
                .execute()

            recipe["contributors"] = contributors_response.data or []
            return recipe
        except Exception as e:
            logger.error(f"Error fetching recipe with contributors: {str(e)}")
            raise

    async def get_user_recipes(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        include_public: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get recipes created by a user

        Optimized to select only fields needed for list view (excludes heavy JSONB arrays)
        """
        try:
            # Select only fields needed for list view (excludes ingredients & instructions)
            query = self.supabase.table(self.table_name)\
                .select("""
                    id, title, description, image_url,
                    servings, difficulty, tags, categories,
                    prep_time_minutes, cook_time_minutes, total_time_minutes,
                    created_by, is_public, fork_count, created_at
                """)\
                .eq("created_by", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user recipes: {str(e)}")
            raise

    async def get_public_recipes(
        self,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get public recipes with optional filters"""
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("is_public", True)\
                .order("created_at", desc=True)

            # Apply additional filters
            if filters:
                if "difficulty" in filters:
                    query = query.eq("difficulty", filters["difficulty"])
                if "tags" in filters and filters["tags"]:
                    query = query.contains("tags", filters["tags"])
                if "categories" in filters and filters["categories"]:
                    query = query.contains("categories", filters["categories"])

            response = query.limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching public recipes: {str(e)}")
            raise

    async def search_recipes(
        self,
        user_id: Optional[str],
        search_query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search recipes using full-text search"""
        try:
            # Build search query
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .or_(f"title.ilike.%{search_query}%,description.ilike.%{search_query}%")

            # Include public recipes and user's own recipes
            if user_id:
                query = query.or_(f"is_public.eq.true,created_by.eq.{user_id}")
            else:
                query = query.eq("is_public", True)

            response = query.limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error searching recipes: {str(e)}")
            raise

    async def fork_recipe(
        self,
        original_recipe_id: str,
        new_recipe_data: Dict[str, Any],
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fork a recipe (create a copy with attribution)"""
        try:
            # Get original recipe
            original = await self.get_by_id(original_recipe_id)
            if not original:
                return None

            # Create forked recipe
            forked_recipe = await self.create(new_recipe_data)
            if not forked_recipe:
                return None

            # Update fork count on original
            await self.supabase.table(self.table_name)\
                .update({"fork_count": original["fork_count"] + 1})\
                .eq("id", original_recipe_id)\
                .execute()

            # Get original contributors
            original_contributors = self.supabase.table("recipe_contributors")\
                .select("*")\
                .eq("recipe_id", original_recipe_id)\
                .order("order")\
                .execute()

            # Add contributors to forked recipe
            contributors = []
            order = 0

            # Add original contributors
            if original_contributors.data:
                for contrib in original_contributors.data:
                    contributors.append({
                        "recipe_id": forked_recipe["id"],
                        "user_id": contrib["user_id"],
                        "contribution_type": contrib["contribution_type"],
                        "order": order
                    })
                    order += 1

            # Add current user as fork contributor
            contributors.append({
                "recipe_id": forked_recipe["id"],
                "user_id": user_id,
                "contribution_type": "fork",
                "order": order
            })

            # Insert all contributors
            if contributors:
                self.supabase.table("recipe_contributors").insert(contributors).execute()

            return forked_recipe
        except Exception as e:
            logger.error(f"Error forking recipe: {str(e)}")
            raise

    async def get_recipe_forks(self, recipe_id: str) -> List[Dict[str, Any]]:
        """Get all forks of a recipe"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("original_recipe_id", recipe_id)\
                .eq("is_public", True)\
                .order("created_at", desc=True)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching recipe forks: {str(e)}")
            raise

    async def increment_fork_count(self, recipe_id: str) -> bool:
        """Increment fork count for a recipe"""
        try:
            recipe = await self.get_by_id(recipe_id)
            if not recipe:
                return False

            await self.update(recipe_id, {"fork_count": recipe["fork_count"] + 1})
            return True
        except Exception as e:
            logger.error(f"Error incrementing fork count: {str(e)}")
            raise
