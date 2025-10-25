"""
OpenAI service for AI-powered recipe processing
Easily replaceable with other AI providers
"""
from typing import Dict, Any, List, Optional
import json
import logging
from openai import OpenAI

from app.core.config import get_settings
from app.domain.models import Recipe, Ingredient, Instruction

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIService:
    """Service for OpenAI API interactions"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, organization=settings.OPENAI_ORGANIZATION_ID, project=settings.OPENAI_PROJECT_ID)
        self.model = "gpt-4o"  # Using GPT-4

    def normalize_recipe(
        self,
        raw_content: str,
        source_type: str,
        existing_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Normalize raw recipe content into structured format.
        Fills in missing information intelligently.

        Args:
            raw_content: Raw text content (transcript, OCR, pasted text, etc.)
            source_type: Type of source (video, photo, voice, url, paste)
            existing_data: Any existing structured data to merge

        Returns:
            Normalized recipe data
        """
        try:
            system_prompt = """You are a professional recipe parser and normalizer.
Your task is to extract recipe information from raw content and structure it properly.

IMPORTANT RULES:
1. Extract ALL ingredients with quantities and units
2. Break down instructions into clear, numbered steps
3. Estimate missing timing information based on the recipe
4. Assign appropriate difficulty level (easy, medium, hard)
5. Add relevant tags and categories
6. If servings are not specified, make a reasonable estimate
7. If prep/cook times are not mentioned, estimate based on the recipe complexity
8. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "title": "Recipe name",
    "description": "Brief description",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2, "unit": "cups", "notes": "optional notes", "group": "optional group like 'For the sauce'"}
    ],
    "instructions": [
        {"step_number": 1, "text": "instruction text", "timer_minutes": null or number}
    ],
    "servings": 4,
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"],
    "categories": ["category1"],
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "total_time_minutes": 45
}"""

            user_prompt = f"""Parse this recipe from {source_type}:

{raw_content}

{f'Existing data to merge: {json.dumps(existing_data)}' if existing_data else ''}

Extract and normalize into JSON format."""

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

            # Validate and structure the response
            normalized = self._validate_and_structure(result)

            logger.info(f"Successfully normalized recipe: {normalized.get('title', 'Unknown')}")
            return normalized

        except Exception as e:
            logger.error(f"Error normalizing recipe: {str(e)}")
            raise

    def _validate_and_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure all required fields are present"""
        normalized = {
            "title": data.get("title", "Untitled Recipe"),
            "description": data.get("description"),
            "ingredients": data.get("ingredients", []),
            "instructions": data.get("instructions", []),
            "servings": data.get("servings"),
            "difficulty": data.get("difficulty"),
            "tags": data.get("tags", []),
            "categories": data.get("categories", []),
            "prep_time_minutes": data.get("prep_time_minutes"),
            "cook_time_minutes": data.get("cook_time_minutes"),
            "total_time_minutes": data.get("total_time_minutes"),
        }

        # Ensure step numbers are sequential
        if normalized["instructions"]:
            for i, instruction in enumerate(normalized["instructions"]):
                instruction["step_number"] = i + 1

        return normalized

    def natural_language_search(
        self,
        query: str,
        recipes: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[str]:
        """
        Use AI to understand natural language search and rank recipes.

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
                    "ingredients": [ing.get("name", "") for ing in recipe.get("ingredients", [])][:10]  # First 10 ingredients
                })

            system_prompt = """You are a recipe search assistant.
Given a natural language query and a list of recipes, rank the recipes by relevance.
Return ONLY a JSON array of recipe IDs in order of relevance."""

            user_prompt = f"""Query: "{query}"

Recipes:
{json.dumps(recipes_summary, indent=2)}

Return the IDs of the most relevant recipes in order, up to {limit} results.
Format: ["id1", "id2", "id3", ...]"""

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

    def enhance_recipe_image_description(self, image_url: str) -> str:
        """
        Use GPT-4 Vision to describe a recipe image.
        This can help with recipe extraction from photos.

        Args:
            image_url: URL of the recipe image

        Returns:
            Description of what's in the image
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this recipe image in detail. Include visible ingredients, cooking steps, and any text you can read."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return ""
