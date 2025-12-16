"""
OpenAI service for AI-powered recipe processing.

NOTE: This service has been deprecated for most extraction operations.
The GeminiService is now used for recipe extraction and normalization.

This service is kept for:
1. natural_language_search (legacy endpoint)
2. Any future OpenAI-specific features

For recipe extraction, use GeminiService instead.
"""
from typing import Dict, Any, List
import json
import logging
from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIService:
    """
    Service for OpenAI API interactions.

    DEPRECATED for extraction - Use GeminiService for recipe extraction.
    Kept for legacy natural language search feature.
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORGANIZATION_ID,
            project=settings.OPENAI_PROJECT_ID
        )
        self.model = "gpt-4o-mini"

    def natural_language_search(
        self,
        query: str,
        recipes: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[str]:
        """
        Use AI to understand natural language search and rank recipes.

        NOTE: This is a legacy feature. Consider using database full-text search
        or vector similarity search for better performance.

        Args:
            query: Natural language search query
            recipes: List of recipe objects to search through
            limit: Maximum number of results

        Returns:
            List of recipe IDs ranked by relevance
        """
        try:
            # Create a simplified representation of recipes for the AI
            recipes_summary = []
            for recipe in recipes:
                recipes_summary.append({
                    "id": recipe["id"],
                    "title": recipe["title"],
                    "description": recipe.get("description", ""),
                    "tags": recipe.get("tags", []),
                    "categories": recipe.get("categories", []),
                    "difficulty": recipe.get("difficulty"),
                    "total_time_minutes": recipe.get("total_time_minutes"),
                    "ingredients": [ing.get("name", "") for ing in recipe.get("ingredients", [])][:10]
                })

            system_prompt = """You are a recipe search assistant.
Given a natural language query and a list of recipes, rank the recipes by relevance.
Return ONLY a JSON object with a "recipe_ids" array of recipe IDs in order of relevance."""

            user_prompt = f"""Query: "{query}"

Recipes:
{json.dumps(recipes_summary, indent=2)}

Return the IDs of the most relevant recipes in order, up to {limit} results.
Format: {{"recipe_ids": ["id1", "id2", "id3", ...]}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content)

            # Extract IDs from various possible response formats
            if isinstance(result, list):
                return result[:limit]
            elif "recipe_ids" in result:
                return result["recipe_ids"][:limit]
            elif "ids" in result:
                return result["ids"][:limit]
            else:
                # Fallback: return first value if it's a list
                for value in result.values():
                    if isinstance(value, list):
                        return value[:limit]

            return []

        except Exception as e:
            logger.error(f"Error in natural language search: {str(e)}")
            # Fallback: simple text matching
            return [r["id"] for r in recipes if query.lower() in r["title"].lower()][:limit]
