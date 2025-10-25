"""
Cookbook repository for database operations
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CookbookRepository(BaseRepository):
    """Repository for cookbook operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "cookbooks")

    async def get_user_cookbooks(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all cookbooks for a user"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user cookbooks: {str(e)}")
            raise

    async def get_with_details(self, cookbook_id: str) -> Optional[Dict[str, Any]]:
        """Get cookbook with folders and recipes"""
        try:
            # Get cookbook
            cookbook = await self.get_by_id(cookbook_id)
            if not cookbook:
                return None

            # Get folders
            folders_response = self.supabase.table("cookbook_folders")\
                .select("*")\
                .eq("cookbook_id", cookbook_id)\
                .order("order")\
                .execute()

            # Get recipes
            recipes_response = self.supabase.table("cookbook_recipes")\
                .select("*, recipes(*)")\
                .eq("cookbook_id", cookbook_id)\
                .order("order")\
                .execute()

            cookbook["folders"] = folders_response.data or []
            cookbook["recipes"] = [r["recipes"] for r in (recipes_response.data or []) if r.get("recipes")]

            return cookbook
        except Exception as e:
            logger.error(f"Error fetching cookbook with details: {str(e)}")
            raise

    async def add_recipe(
        self,
        cookbook_id: str,
        recipe_id: str,
        folder_id: Optional[str] = None
    ) -> bool:
        """Add a recipe to a cookbook"""
        try:
            # Add to cookbook_recipes
            self.supabase.table("cookbook_recipes").insert({
                "cookbook_id": cookbook_id,
                "recipe_id": recipe_id
            }).execute()

            # If folder specified, add to folder_recipes
            if folder_id:
                self.supabase.table("folder_recipes").insert({
                    "folder_id": folder_id,
                    "recipe_id": recipe_id
                }).execute()

            # Update recipe count
            await self._update_recipe_count(cookbook_id)

            return True
        except Exception as e:
            logger.error(f"Error adding recipe to cookbook: {str(e)}")
            raise

    async def remove_recipe(
        self,
        cookbook_id: str,
        recipe_id: str
    ) -> bool:
        """Remove a recipe from a cookbook"""
        try:
            # Remove from cookbook_recipes
            self.supabase.table("cookbook_recipes")\
                .delete()\
                .eq("cookbook_id", cookbook_id)\
                .eq("recipe_id", recipe_id)\
                .execute()

            # Remove from all folders in this cookbook
            folders = self.supabase.table("cookbook_folders")\
                .select("id")\
                .eq("cookbook_id", cookbook_id)\
                .execute()

            if folders.data:
                folder_ids = [f["id"] for f in folders.data]
                self.supabase.table("folder_recipes")\
                    .delete()\
                    .in_("folder_id", folder_ids)\
                    .eq("recipe_id", recipe_id)\
                    .execute()

            # Update recipe count
            await self._update_recipe_count(cookbook_id)

            return True
        except Exception as e:
            logger.error(f"Error removing recipe from cookbook: {str(e)}")
            raise

    async def _update_recipe_count(self, cookbook_id: str):
        """Update the recipe count for a cookbook"""
        try:
            # Count recipes in cookbook
            response = self.supabase.table("cookbook_recipes")\
                .select("id", count="exact")\
                .eq("cookbook_id", cookbook_id)\
                .execute()

            count = response.count or 0

            # Update cookbook
            await self.update(cookbook_id, {"recipe_count": count})
        except Exception as e:
            logger.error(f"Error updating recipe count: {str(e)}")


class CookbookFolderRepository(BaseRepository):
    """Repository for cookbook folder operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "cookbook_folders")

    async def get_folder_recipes(
        self,
        folder_id: str
    ) -> List[Dict[str, Any]]:
        """Get all recipes in a folder"""
        try:
            response = self.supabase.table("folder_recipes")\
                .select("*, recipes(*)")\
                .eq("folder_id", folder_id)\
                .order("order")\
                .execute()

            return [r["recipes"] for r in (response.data or []) if r.get("recipes")]
        except Exception as e:
            logger.error(f"Error fetching folder recipes: {str(e)}")
            raise

    async def get_subfolders(
        self,
        parent_folder_id: str
    ) -> List[Dict[str, Any]]:
        """Get all subfolders of a folder"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("parent_folder_id", parent_folder_id)\
                .order("order")\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching subfolders: {str(e)}")
            raise
