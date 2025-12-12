"""
Translation service for recipe translations
Handles translating recipes between languages using AI
"""
import json
import logging
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from supabase import Client

from app.core.config import get_settings
from app.repositories.translation_repository import TranslationRepository
from app.repositories.recipe_repository import RecipeRepository

logger = logging.getLogger(__name__)
settings = get_settings()

# Language name mapping for prompts
LANGUAGE_NAMES = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
}


class TranslationService:
    """Service for translating recipes between languages"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.translation_repo = TranslationRepository(supabase)
        self.recipe_repo = RecipeRepository(supabase)
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORGANIZATION_ID,
            project=settings.OPENAI_PROJECT_ID
        )
        self.model = "gpt-4o-mini"  # Cost-effective model for translation

    def _get_language_name(self, code: str) -> str:
        """Get human-readable language name from ISO code"""
        return LANGUAGE_NAMES.get(code, code.upper())

    async def translate_recipe(
        self,
        recipe: Dict[str, Any],
        target_language: str
    ) -> Dict[str, Any]:
        """
        Translate recipe content to target language using AI.

        Args:
            recipe: Recipe dict with title, description, ingredients, instructions
            target_language: ISO 639-1 language code

        Returns:
            Dict with translated title, description, ingredients, instructions
        """
        source_language = recipe.get("language", "en")
        source_lang_name = self._get_language_name(source_language)
        target_lang_name = self._get_language_name(target_language)

        try:
            system_prompt = f"""You are a professional culinary translator specializing in recipe translation.
Translate the following recipe from {source_lang_name} to {target_lang_name}.

TRANSLATION RULES:
1. Translate: title, description, ingredient names, ingredient notes, instruction titles, instruction descriptions
2. DO NOT translate or modify: quantities, units, timings, step numbers, group names structure
3. Keep ingredient group names translated (e.g., "For the sauce" → "Pour la sauce" in French)
4. Keep instruction group names translated
5. Preserve all formatting and structure
6. Use natural culinary terminology in the target language
7. Return ONLY valid JSON, no markdown formatting

Response format:
{{
    "title": "Translated recipe title",
    "description": "Translated description or null",
    "ingredients": [
        {{"name": "translated ingredient name", "quantity": 2, "unit": "cups", "notes": "translated notes or null", "group": "translated group or null"}}
    ],
    "instructions": [
        {{"step_number": 1, "title": "Translated step title", "description": "Translated instruction text", "timer_minutes": 5, "group": "translated group or null"}}
    ]
}}"""

            # Build the recipe content to translate
            recipe_content = {
                "title": recipe.get("title", ""),
                "description": recipe.get("description"),
                "ingredients": recipe.get("ingredients", []),
                "instructions": recipe.get("instructions", [])
            }

            user_prompt = f"""Translate this recipe to {target_lang_name}:

{json.dumps(recipe_content, ensure_ascii=False, indent=2)}

Return the translated recipe as JSON."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content)

            # Log usage for cost tracking
            usage = response.usage
            cost = self._calculate_cost(usage)
            logger.info(
                f"Translated recipe '{recipe.get('title')}' from {source_language} to {target_language}. "
                f"Tokens: {usage.total_tokens}, Cost: ${cost:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Error translating recipe: {str(e)}")
            raise

    def _calculate_cost(self, usage) -> float:
        """Calculate estimated cost for GPT-4o-mini"""
        # Pricing per 1M tokens (as of Jan 2025)
        input_price = 0.15  # per 1M tokens
        output_price = 0.60  # per 1M tokens

        cost = (
            (usage.prompt_tokens / 1_000_000) * input_price +
            (usage.completion_tokens / 1_000_000) * output_price
        )
        return cost

    async def get_or_create_translation(
        self,
        recipe_id: str,
        target_language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing translation or create a new one.

        Args:
            recipe_id: Recipe ID
            target_language: ISO 639-1 language code

        Returns:
            Translation dict or None if recipe not found
        """
        try:
            # Check if translation already exists
            existing = await self.translation_repo.get_translation(recipe_id, target_language)
            if existing:
                logger.debug(f"Found cached translation for recipe {recipe_id} in {target_language}")
                return existing

            # Get the original recipe
            recipe = await self.recipe_repo.get_by_id(recipe_id)
            if not recipe:
                logger.error(f"Recipe {recipe_id} not found")
                return None

            # If recipe is already in target language, no translation needed
            if recipe.get("language") == target_language:
                logger.debug(f"Recipe {recipe_id} is already in {target_language}")
                return None

            # Translate the recipe
            translated = await self.translate_recipe(recipe, target_language)

            # Cache the translation
            translation = await self.translation_repo.create_translation(
                recipe_id=recipe_id,
                language=target_language,
                title=translated["title"],
                description=translated.get("description"),
                ingredients=translated.get("ingredients", []),
                instructions=translated.get("instructions", [])
            )

            return translation

        except Exception as e:
            logger.error(f"Error in get_or_create_translation: {str(e)}")
            raise

    async def get_recipe_in_language(
        self,
        recipe: Dict[str, Any],
        target_language: str,
        create_if_missing: bool = False
    ) -> Dict[str, Any]:
        """
        Return recipe with content in target language.

        If recipe's original language matches target, returns as-is.
        Otherwise, returns translation if it exists.

        Args:
            recipe: Original recipe dict
            target_language: ISO 639-1 language code
            create_if_missing: If True, create translation if it doesn't exist (costs money).
                              If False, return original recipe if no translation exists.

        Returns:
            Recipe dict with content in target language (or original if no translation)
        """
        recipe_language = recipe.get("language", "en")

        # If same language, return original
        if recipe_language == target_language:
            return {
                **recipe,
                "displayed_language": target_language,
                "is_translated": False
            }

        # Get translation (create only if explicitly requested)
        if create_if_missing:
            translation = await self.get_or_create_translation(
                recipe["id"],
                target_language
            )
        else:
            # Only fetch existing translation, don't create new one
            translation = await self.translation_repo.get_translation(
                recipe["id"],
                target_language
            )

        if not translation:
            # No translation available, return original
            logger.debug(f"No translation found for recipe {recipe['id']} in {target_language}")
            return {
                **recipe,
                "displayed_language": recipe_language,
                "is_translated": False
            }

        # Debug: Log translation content
        logger.info(f"Translation found for recipe {recipe['id']} in {target_language}")
        logger.debug(f"Translation keys: {translation.keys()}")
        logger.debug(f"Translation ingredients count: {len(translation.get('ingredients', []))}")
        logger.debug(f"Translation instructions count: {len(translation.get('instructions', []))}")

        # Merge translated content into recipe
        translated_recipe = {
            **recipe,
            "title": translation["title"],
            "description": translation.get("description"),
            "ingredients": translation.get("ingredients", recipe.get("ingredients", [])),
            "instructions": translation.get("instructions", recipe.get("instructions", [])),
            "displayed_language": target_language,
            "is_translated": True
        }

        logger.debug(f"Merged recipe ingredients count: {len(translated_recipe.get('ingredients', []))}")
        logger.debug(f"Merged recipe instructions count: {len(translated_recipe.get('instructions', []))}")

        return translated_recipe

    async def invalidate_translations(self, recipe_id: str) -> int:
        """
        Delete all cached translations for a recipe.
        Should be called when a recipe is edited.

        Args:
            recipe_id: Recipe ID

        Returns:
            Number of translations deleted
        """
        try:
            count = await self.translation_repo.delete_translations(recipe_id)
            if count > 0:
                logger.info(f"Invalidated {count} translations for recipe {recipe_id}")
            return count
        except Exception as e:
            logger.error(f"Error invalidating translations: {str(e)}")
            raise

    async def get_available_languages(self, recipe_id: str) -> Dict[str, Any]:
        """
        Get the original language and available translations for a recipe.

        Args:
            recipe_id: Recipe ID

        Returns:
            Dict with 'original' language and 'translations' list
        """
        try:
            # Get recipe's original language
            recipe = await self.recipe_repo.get_by_id(recipe_id)
            if not recipe:
                return {"original": None, "translations": []}

            original_language = recipe.get("language", "en")

            # Get available translations
            translations = await self.translation_repo.get_available_languages(recipe_id)

            return {
                "original": original_language,
                "translations": translations
            }
        except Exception as e:
            logger.error(f"Error getting available languages: {str(e)}")
            raise
