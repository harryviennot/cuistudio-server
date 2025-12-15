"""
Gemini service for AI-powered recipe extraction and normalization.
Uses Gemini 2.5 Flash Lite for fast, cost-effective recipe processing.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional

import google.generativeai as genai

from app.core.config import get_settings
from app.domain.exceptions import NotARecipeError

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiService:
    """Service for Google Gemini API interactions for recipe extraction."""

    # Model configuration
    # gemini-2.5-flash-lite is fastest based on benchmarks
    # Use preview version which is more widely available
    MODEL_NAME = "gemini-2.5-flash-lite"

    # Pricing per 1M tokens (as of Dec 2024)
    PRICING = {
        "input": 0.075,   # $0.075 per 1M input tokens
        "output": 0.30,   # $0.30 per 1M output tokens
    }

    def __init__(self):
        """Initialize Gemini service with API key from settings."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required for GeminiService. "
                "Please set it in your .env file."
            )

        genai.configure(api_key=api_key)
        self._genai = genai
        logger.info(f"GeminiService initialized with model: {self.MODEL_NAME}")

    def _get_generation_config(self, temperature: float = 0.3, max_tokens: int = 2000):
        """Get generation config for Gemini API calls."""
        return self._genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json"
        )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage."""
        return (
            (input_tokens / 1_000_000) * self.PRICING["input"] +
            (output_tokens / 1_000_000) * self.PRICING["output"]
        )

    def _validate_and_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure all required fields are present."""
        normalized = {
            "title": data.get("title", "Untitled Recipe"),
            "description": data.get("description"),
            "language": data.get("language", "en"),
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

        # Clean up ingredients: remove whitespace-only units and quantities
        if normalized["ingredients"]:
            for ingredient in normalized["ingredients"]:
                if "unit" in ingredient:
                    unit = ingredient.get("unit")
                    if isinstance(unit, str) and not unit.strip():
                        ingredient["unit"] = None
                if "quantity" in ingredient:
                    quantity = ingredient.get("quantity")
                    if isinstance(quantity, str) and not quantity.strip():
                        ingredient["quantity"] = None

        # Ensure step numbers are sequential
        if normalized["instructions"]:
            for i, instruction in enumerate(normalized["instructions"]):
                instruction["step_number"] = i + 1

        return normalized

    async def normalize_recipe(
        self,
        raw_content: str,
        source_type: str,
        existing_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Normalize raw recipe content into structured format using Gemini 2.5 Flash Lite.

        Args:
            raw_content: Raw text content (transcript, OCR, scraped text, etc.)
            source_type: Type of source (video, photo, voice, url, paste)
            existing_data: Any existing structured data to merge

        Returns:
            Normalized recipe data with extraction stats

        Raises:
            NotARecipeError: If content is not a valid recipe
        """
        try:
            system_prompt = """You are a professional recipe parser and normalizer.
Your task is to first determine if the content contains a recipe, then extract and structure it.

IMPORTANT - LANGUAGE PRESERVATION:
Extract the recipe in its ORIGINAL language. Do NOT translate.
If the recipe is in French, return ALL fields in French.
If in Spanish, return ALL fields in Spanish.
Keep title, description, ingredients, and instructions in the same original language.

STEP 1 - CONTENT CLASSIFICATION:
Determine if this content is actually a recipe. A recipe must contain:
- Food/dish being prepared
- At least some ingredients OR cooking/preparation instructions

NOT recipes include:
- Random videos (cat videos, vlogs, music, etc.)
- Non-food content (landscapes, people, objects)
- General text without cooking instructions
- Product/restaurant reviews without recipes
- Food photos without recipes attached

STEP 2 - IF RECIPE, EXTRACT DATA:
1. Extract ALL ingredients with quantities and units
2. Group ingredients logically by recipe sections:
   - "For the [component]" - e.g., "For the duck", "For the sauce", "For the pasta"
   - "For the garnish" - garnish/decoration ingredients
   - "To taste" - salt, pepper, and seasonings added to preference
   - Use null if no logical groups exist
3. Break down instructions into clear, numbered steps with a title and description
4. Each instruction should have a concise title and detailed description
5. Group instructions logically by recipe sections:
   - "For the [component]" - e.g., "For the duck", "For the sauce", "For the pasta"
   - "Assembly" - final plating/serving steps
   - "For the garnish" - garnish preparation
   - Use null if no logical groups exist
6. TIMER BEHAVIOR - IMPORTANT:
   - "timer_minutes" should ONLY be set when the user needs to SET AN ACTUAL TIMER
   - Include timer for: baking, simmering, boiling, resting, marinating, roasting, steeping
   - Do NOT include timer for active tasks like: "chop vegetables", "stir sauce", "mix ingredients"
   - Use null if no timer is needed for that step
7. Assign appropriate difficulty level (easy, medium, hard)
8. Add relevant tags and categories
9. If servings are not specified, make a reasonable estimate
10. If prep/cook times are not mentioned, estimate based on the recipe complexity
11. DETECT the primary language of the recipe (en, fr, es, de, it, etc.)
12. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "is_recipe": true or false,
    "rejection_reason": "Brief explanation if not a recipe (null if is_recipe=true)",

    // Only include the following fields if is_recipe=true:
    "title": "Recipe name (in original language)",
    "description": "Brief description (in original language)",
    "language": "en",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2, "unit": "cups", "notes": "optional notes", "group": "optional group like 'For the sauce'"}
    ],
    "instructions": [
        {"step_number": 1, "title": "Step title", "description": "Detailed instruction text", "timer_minutes": null or number, "group": "optional group like 'For the sauce' or 'Assembly'"}
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

Extract and normalize into JSON format. Remember to preserve the original language."""

            # Create model with system instruction
            model = self._genai.GenerativeModel(
                model_name=self.MODEL_NAME,
                generation_config=self._get_generation_config(),
                system_instruction=system_prompt
            )

            # Run in thread pool since the SDK is synchronous
            def _generate():
                return model.generate_content(user_prompt)

            response = await asyncio.to_thread(_generate)

            # Parse response
            result = json.loads(response.text)

            # Check if content is a recipe
            if not result.get("is_recipe", True):
                rejection_reason = result.get("rejection_reason", "Content does not appear to be a recipe")
                logger.info(f"Content not a recipe: {rejection_reason}")
                raise NotARecipeError(message=rejection_reason)

            # Validate and structure the response
            normalized = self._validate_and_structure(result)

            # Calculate token usage (estimate output tokens from response length)
            input_tokens = model.count_tokens(system_prompt + user_prompt).total_tokens
            output_tokens = len(response.text) // 4  # Rough estimate

            # Add usage statistics
            normalized["_extraction_stats"] = {
                "model": self.MODEL_NAME,
                "provider": "gemini",
                "method": "normalize",
                "source_type": source_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost_usd": self._calculate_cost(input_tokens, output_tokens)
            }

            logger.info(f"Successfully normalized recipe: {normalized.get('title', 'Unknown')}")
            logger.info(f"Token usage: {input_tokens + output_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

            return normalized

        except NotARecipeError:
            raise
        except Exception as e:
            logger.error(f"Error normalizing recipe with Gemini: {str(e)}")
            raise

    async def extract_recipe_from_ocr(
        self,
        ocr_text: str,
        image_count: int = 1
    ) -> Dict[str, Any]:
        """
        Extract structured recipe from OCR text (for photo extraction).
        This is an OCR-only approach - no Vision API, just text processing.

        Args:
            ocr_text: Raw OCR text extracted from recipe image(s)
            image_count: Number of images the OCR was extracted from

        Returns:
            Structured recipe data with extraction stats

        Raises:
            NotARecipeError: If content is not a valid recipe
        """
        try:
            system_prompt = """You are a professional recipe extraction expert.

IMPORTANT - LANGUAGE PRESERVATION:
Extract the recipe in its ORIGINAL language. Do NOT translate.
If the recipe is in French, return ALL fields in French.
If in Spanish, return ALL fields in Spanish.
Keep title, description, ingredients, and instructions in the same original language.

STEP 1 - CONTENT CLASSIFICATION:
Analyze the OCR text to determine what type of content this is:
- "recipe_card": Recipe text with ingredients and/or instructions
- "food_photo": Description suggests a food photo without recipe text (unlikely from OCR)
- "non_food": Not food-related content

STEP 2 - EXTRACTION:

If "recipe_card":
- Extract the recipe from the OCR text
- Fix common OCR errors: misread characters (0/O, 1/l/I), merged words, spacing issues
- Structure into proper recipe format

If "non_food":
- Return is_recipe: false with a rejection reason

EXTRACTION RULES:
1. Extract COMPLETE ingredients: quantity + unit + name (e.g., "2 cups flour" not "2 cups")
2. Group ingredients logically based on recipe sections:
   - "For the [main dish]" - main ingredients (e.g., "For the soup", "For the duck")
   - "For the [sauce/topping]" - sauce or topping ingredients
   - "For the garnish" - garnish/decoration ingredients
   - "To taste" - salt, pepper, and seasonings added to preference
   - If no logical groups exist, use null for the group field
3. Number all instruction steps sequentially
4. Each instruction should have a concise title and detailed description
5. Group instructions logically based on recipe sections
6. TIMER BEHAVIOR - IMPORTANT:
   - "timer_minutes" should ONLY be set when the user needs to SET AN ACTUAL TIMER
   - Include timer for: baking, simmering, boiling, resting, marinating, roasting, steeping
   - Do NOT include timer for active tasks like: "chop vegetables", "stir sauce", "mix ingredients"
   - Use null if no timer is needed for that step
7. If servings not visible, estimate based on ingredient quantities
8. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "content_type": "recipe_card" | "non_food",
    "is_recipe": true or false,
    "rejection_reason": "Brief explanation (if non_food)",

    // Only include these if is_recipe=true:
    "title": "Recipe name (in original language)",
    "description": "Brief description of the dish (in original language)",
    "language": "en",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2.0, "unit": "cups", "notes": "optional prep notes", "group": "For the soup"}
    ],
    "instructions": [
        {"step_number": 1, "title": "Step title", "description": "Detailed instruction text", "timer_minutes": null or 5, "group": "For the soup"}
    ],
    "servings": 4,
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"],
    "categories": ["category1"],
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "total_time_minutes": 45
}"""

            image_context = f"from {image_count} image(s)" if image_count > 1 else ""
            user_prompt = f"""Extract a recipe from this OCR text {image_context} (may contain OCR errors that need fixing):

---OCR TEXT---
{ocr_text}
---END OCR---

Task:
1. First, classify if this is recipe content or not
2. If recipe: Extract and structure the recipe, fixing any OCR errors
3. If not recipe: Return is_recipe: false with rejection reason
4. Return structured JSON following the specified format
5. IMPORTANT: Preserve the original language - do not translate"""

            # Create model with system instruction
            model = self._genai.GenerativeModel(
                model_name=self.MODEL_NAME,
                generation_config=self._get_generation_config(),
                system_instruction=system_prompt
            )

            # Run in thread pool since the SDK is synchronous
            def _generate():
                return model.generate_content(user_prompt)

            response = await asyncio.to_thread(_generate)

            # Parse response
            result = json.loads(response.text)

            # Check if content is a recipe
            if not result.get("is_recipe", True):
                rejection_reason = result.get("rejection_reason", "Text does not contain a recipe")
                content_type = result.get("content_type", "unknown")
                logger.info(f"OCR text not a recipe (type: {content_type}): {rejection_reason}")
                raise NotARecipeError(message=rejection_reason)

            # Validate and structure the response
            normalized = self._validate_and_structure(result)

            # Calculate token usage
            input_tokens = model.count_tokens(system_prompt + user_prompt).total_tokens
            output_tokens = len(response.text) // 4

            # Add usage statistics
            normalized["_extraction_stats"] = {
                "model": self.MODEL_NAME,
                "provider": "gemini",
                "method": "ocr_extraction",
                "content_type": result.get("content_type", "recipe_card"),
                "image_count": image_count,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost_usd": self._calculate_cost(input_tokens, output_tokens)
            }

            logger.info(f"Successfully extracted recipe from OCR: {normalized.get('title', 'Unknown')}")
            logger.info(f"Token usage: {input_tokens + output_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

            return normalized

        except NotARecipeError:
            raise
        except Exception as e:
            logger.error(f"Error extracting recipe from OCR with Gemini: {str(e)}")
            raise
