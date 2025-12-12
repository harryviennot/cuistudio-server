"""
Translation repository for recipe translations database operations
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class TranslationRepository(BaseRepository):
    """Repository for recipe translation operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "recipe_translations")

    async def get_translation(
        self,
        recipe_id: str,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a translation for a recipe in a specific language.

        Args:
            recipe_id: Recipe ID
            language: ISO 639-1 language code (e.g., 'en', 'fr')

        Returns:
            Translation dict or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("recipe_id", recipe_id)\
                .eq("language", language)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting translation for recipe {recipe_id} in {language}: {str(e)}")
            raise

    async def create_translation(
        self,
        recipe_id: str,
        language: str,
        title: str,
        description: Optional[str],
        ingredients: List[Dict[str, Any]],
        instructions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a new translation for a recipe.

        Args:
            recipe_id: Recipe ID
            language: ISO 639-1 language code
            title: Translated title
            description: Translated description
            ingredients: Translated ingredients list
            instructions: Translated instructions list

        Returns:
            Created translation dict
        """
        try:
            data = {
                "recipe_id": recipe_id,
                "language": language,
                "title": title,
                "description": description,
                "ingredients": ingredients,
                "instructions": instructions
            }
            response = self.supabase.table(self.table_name).insert(data).execute()
            logger.info(f"Created translation for recipe {recipe_id} in {language}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating translation for recipe {recipe_id} in {language}: {str(e)}")
            raise

    async def upsert_translation(
        self,
        recipe_id: str,
        language: str,
        title: str,
        description: Optional[str],
        ingredients: List[Dict[str, Any]],
        instructions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create or update a translation for a recipe.

        Args:
            recipe_id: Recipe ID
            language: ISO 639-1 language code
            title: Translated title
            description: Translated description
            ingredients: Translated ingredients list
            instructions: Translated instructions list

        Returns:
            Upserted translation dict
        """
        try:
            data = {
                "recipe_id": recipe_id,
                "language": language,
                "title": title,
                "description": description,
                "ingredients": ingredients,
                "instructions": instructions
            }
            response = self.supabase.table(self.table_name)\
                .upsert(data, on_conflict="recipe_id,language")\
                .execute()
            logger.info(f"Upserted translation for recipe {recipe_id} in {language}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error upserting translation for recipe {recipe_id} in {language}: {str(e)}")
            raise

    async def delete_translations(self, recipe_id: str) -> int:
        """
        Delete all translations for a recipe (invalidation on edit).

        Args:
            recipe_id: Recipe ID

        Returns:
            Number of translations deleted
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("recipe_id", recipe_id)\
                .execute()
            count = len(response.data) if response.data else 0
            if count > 0:
                logger.info(f"Deleted {count} translations for recipe {recipe_id}")
            return count
        except Exception as e:
            logger.error(f"Error deleting translations for recipe {recipe_id}: {str(e)}")
            raise

    async def delete_translation(self, recipe_id: str, language: str) -> bool:
        """
        Delete a specific translation for a recipe.

        Args:
            recipe_id: Recipe ID
            language: ISO 639-1 language code

        Returns:
            True if deleted, False if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("recipe_id", recipe_id)\
                .eq("language", language)\
                .execute()
            return len(response.data) > 0 if response.data else False
        except Exception as e:
            logger.error(f"Error deleting translation for recipe {recipe_id} in {language}: {str(e)}")
            raise

    async def get_available_languages(self, recipe_id: str) -> List[str]:
        """
        Get list of available translation languages for a recipe.

        Args:
            recipe_id: Recipe ID

        Returns:
            List of ISO 639-1 language codes
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("language")\
                .eq("recipe_id", recipe_id)\
                .execute()
            return [t["language"] for t in (response.data or [])]
        except Exception as e:
            logger.error(f"Error getting available languages for recipe {recipe_id}: {str(e)}")
            raise

    async def get_translations_for_recipe(self, recipe_id: str) -> List[Dict[str, Any]]:
        """
        Get all translations for a recipe.

        Args:
            recipe_id: Recipe ID

        Returns:
            List of translation dicts
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("recipe_id", recipe_id)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting translations for recipe {recipe_id}: {str(e)}")
            raise
