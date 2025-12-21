"""
Gemini service for AI-powered recipe extraction and normalization.
Uses Gemini for text processing, Vision API for images, and audio transcription.
Falls back to GPT-4o-mini if Gemini refuses due to copyright detection.

Feature Flags:
- gemini_3_text_extraction: Use gemini-3-flash-preview instead of gemini-2.5-flash-lite
- gemini_audio_transcription: Use Gemini for audio transcription instead of Whisper
- gemini_image_generation: Use Gemini for image generation instead of Flux
"""
import asyncio
import base64
import json
import logging
import os
import re
from typing import Dict, Any, Optional, List, Union

import google.generativeai as genai
from openai import OpenAI

from app.core.config import get_settings
from app.domain.exceptions import NotARecipeError

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiRecitationError(Exception):
    """Raised when Gemini refuses to process content due to copyright/recitation detection."""
    pass


class GeminiService:
    """Service for Google Gemini API interactions for recipe extraction."""

    # Model configuration - OLD models remain default
    MODEL_TEXT_OLD = "gemini-2.5-flash-lite"       # Default text model
    MODEL_TEXT_NEW = "gemini-3-flash-preview"      # Behind gemini_3_text_extraction flag
    MODEL_AUDIO = "gemini-3-flash-preview"         # Behind gemini_audio_transcription flag
    MODEL_IMAGE_GEN = "gemini-2.0-flash-exp"       # Behind gemini_image_generation flag
    OPENAI_MODEL = "gpt-4o-mini"                   # Fallback model

    # Alias for backward compatibility
    MODEL_NAME = MODEL_TEXT_OLD

    # Pricing per 1M tokens (as of Dec 2024)
    PRICING = {
        "gemini-2.5-flash-lite": {
            "input": 0.075,   # $0.075 per 1M input tokens
            "output": 0.30,   # $0.30 per 1M output tokens
        },
        "gemini-3-flash-preview": {
            "input": 0.50,    # $0.50 per 1M input tokens
            "output": 3.00,   # $3.00 per 1M output tokens
        },
        "gemini-3-flash-preview-audio": {
            "input": 1.00,    # $1.00 per 1M tokens for audio
            "output": 3.00,
        },
        "gemini-2.0-flash-exp": {
            "per_image": 0.039,  # Per generated image
        },
        "gemini": {
            "input": 0.075,   # Default Gemini pricing
            "output": 0.30,
        },
        "openai": {
            "input": 0.15,    # $0.15 per 1M input tokens
            "output": 0.60,   # $0.60 per 1M output tokens
        }
    }

    def __init__(self, feature_flag_service=None):
        """
        Initialize Gemini service with API key from settings.

        Args:
            feature_flag_service: Optional FeatureFlagService for model selection
        """
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required for GeminiService. "
                "Please set it in your .env file."
            )

        genai.configure(api_key=api_key)
        self._genai = genai
        self._feature_flags = feature_flag_service

        # Initialize OpenAI client for fallback
        self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        logger.info(f"GeminiService initialized with models: text={self.MODEL_TEXT_OLD}, fallback={self.OPENAI_MODEL}")

    async def _get_text_model_name(self) -> str:
        """
        Get the text model to use based on feature flag.

        Returns:
            Model name string
        """
        if self._feature_flags:
            try:
                use_new = await self._feature_flags.is_enabled("gemini_3_text_extraction")
                if use_new:
                    return self.MODEL_TEXT_NEW
            except Exception as e:
                logger.warning(f"Failed to check feature flag, using default model: {e}")

        return self.MODEL_TEXT_OLD

    def _get_generation_config(self, temperature: float = 0.3, max_tokens: int = 4000):
        """Get generation config for Gemini API calls."""
        return self._genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json"
        )

    def _calculate_cost(self, input_tokens: int, output_tokens: int, provider: str = "gemini") -> float:
        """Calculate estimated cost based on token usage."""
        pricing = self.PRICING.get(provider, self.PRICING["gemini"])
        return (
            (input_tokens / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"]
        )

    def _is_recitation_error(self, error: Exception) -> bool:
        """Check if error is due to Gemini's copyright/recitation detection."""
        error_str = str(error).lower()
        return (
            "reciting from copyrighted material" in error_str or
            "finish_reason" in error_str and "4" in error_str
        )

    def _parse_servings(self, value: Any) -> Optional[int]:
        """Parse servings value to integer, handling ranges like '4 - 6'."""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            # Handle ranges like "4 - 6" or "4-6" by taking the first number
            match = re.search(r'\d+', value)
            if match:
                return int(match.group())
        return None

    def _parse_time_minutes(self, value: Any) -> Optional[int]:
        """Parse time value to integer."""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            match = re.search(r'\d+', value)
            if match:
                return int(match.group())
        return None

    def _validate_and_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure all required fields are present."""
        normalized = {
            "title": data.get("title", "Untitled Recipe"),
            "description": data.get("description"),
            "language": data.get("language", "en"),
            "ingredients": data.get("ingredients", []),
            "instructions": data.get("instructions", []),
            "servings": self._parse_servings(data.get("servings")),
            "difficulty": data.get("difficulty"),
            "tags": data.get("tags", []),
            "categories": data.get("categories", []),
            "prep_time_minutes": self._parse_time_minutes(data.get("prep_time_minutes")),
            "cook_time_minutes": self._parse_time_minutes(data.get("cook_time_minutes")),
            "resting_time_minutes": self._parse_time_minutes(data.get("resting_time_minutes")),
        }

        # Calculate total_time_minutes from the three timing fields
        prep = normalized["prep_time_minutes"] or 0
        cook = normalized["cook_time_minutes"] or 0
        resting = normalized["resting_time_minutes"] or 0
        normalized["total_time_minutes"] = prep + cook + resting if (prep or cook or resting) else None

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

    async def _normalize_recipe_openai(
        self,
        raw_content: str,
        source_type: str,
        system_prompt: str,
        existing_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fallback: Normalize recipe using GPT-4o-mini when Gemini refuses.
        Uses the same prompts as the Gemini version for consistency.
        """
        logger.info("Using OpenAI GPT-4o-mini fallback for recipe normalization")

        user_prompt = f"""Parse this recipe from {source_type}:

{raw_content}

{f'Existing data to merge: {json.dumps(existing_data)}' if existing_data else ''}

Extract and normalize into JSON format. Remember to preserve the original language."""

        response = await asyncio.to_thread(
            self._openai_client.chat.completions.create,
            model=self.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        result = json.loads(response.choices[0].message.content)

        # Check if content is a recipe
        if not result.get("is_recipe", True):
            rejection_reason = result.get("rejection_reason", "Content does not appear to be a recipe")
            logger.info(f"Content not a recipe (OpenAI fallback): {rejection_reason}")
            raise NotARecipeError(message=rejection_reason)

        # Validate and structure the response
        normalized = self._validate_and_structure(result)

        # Calculate token usage from OpenAI response
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # Add usage statistics
        normalized["_extraction_stats"] = {
            "model": self.OPENAI_MODEL,
            "provider": "openai",
            "method": "normalize",
            "source_type": source_type,
            "fallback": True,
            "fallback_reason": "gemini_recitation_block",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": self._calculate_cost(input_tokens, output_tokens, "openai")
        }

        logger.info(f"Successfully normalized recipe (OpenAI fallback): {normalized.get('title', 'Unknown')}")
        logger.info(f"Token usage: {input_tokens + output_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

        return normalized

    async def _extract_recipe_from_ocr_openai(
        self,
        ocr_text: str,
        system_prompt: str,
        image_count: int = 1
    ) -> Dict[str, Any]:
        """
        Fallback: Extract recipe from OCR using GPT-4o-mini when Gemini refuses.
        Uses the same prompts as the Gemini version for consistency.
        """
        logger.info("Using OpenAI GPT-4o-mini fallback for OCR recipe extraction")

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

        response = await asyncio.to_thread(
            self._openai_client.chat.completions.create,
            model=self.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        result = json.loads(response.choices[0].message.content)

        # Check if content is a recipe
        if not result.get("is_recipe", True):
            rejection_reason = result.get("rejection_reason", "Text does not contain a recipe")
            content_type = result.get("content_type", "unknown")
            logger.info(f"OCR text not a recipe (OpenAI fallback, type: {content_type}): {rejection_reason}")
            raise NotARecipeError(message=rejection_reason)

        # Validate and structure the response
        normalized = self._validate_and_structure(result)

        # Calculate token usage from OpenAI response
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # Add usage statistics
        normalized["_extraction_stats"] = {
            "model": self.OPENAI_MODEL,
            "provider": "openai",
            "method": "ocr_extraction",
            "content_type": result.get("content_type", "recipe_card"),
            "image_count": image_count,
            "fallback": True,
            "fallback_reason": "gemini_recitation_block",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": self._calculate_cost(input_tokens, output_tokens, "openai")
        }

        logger.info(f"Successfully extracted recipe from OCR (OpenAI fallback): {normalized.get('title', 'Unknown')}")
        logger.info(f"Token usage: {input_tokens + output_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

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
    "resting_time_minutes": 0
}

TIMING DEFINITIONS:
- prep_time_minutes: Active preparation time before cooking (chopping, mixing, measuring)
- cook_time_minutes: Active cooking time (baking, frying, boiling, simmering)
- resting_time_minutes: Passive waiting time where no active work is needed (marinating, rising dough, freezing, cooling, resting meat, chilling, proofing). This is NOT prep or cook time.

NOTE: Do NOT include total_time_minutes - it will be calculated automatically."""

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
            # Check if this is a recitation/copyright error - use OpenAI fallback
            if self._is_recitation_error(e):
                logger.warning(f"Gemini blocked due to copyright detection, falling back to OpenAI: {str(e)}")
                return await self._normalize_recipe_openai(
                    raw_content, source_type, system_prompt, existing_data
                )
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
    "resting_time_minutes": 0
}

TIMING DEFINITIONS:
- prep_time_minutes: Active preparation time before cooking (chopping, mixing, measuring)
- cook_time_minutes: Active cooking time (baking, frying, boiling, simmering)
- resting_time_minutes: Passive waiting time where no active work is needed (marinating, rising dough, freezing, cooling, resting meat, chilling, proofing). This is NOT prep or cook time.

NOTE: Do NOT include total_time_minutes - it will be calculated automatically."""

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
            # Check if this is a recitation/copyright error - use OpenAI fallback
            if self._is_recitation_error(e):
                logger.warning(f"Gemini blocked due to copyright detection, falling back to OpenAI: {str(e)}")
                return await self._extract_recipe_from_ocr_openai(
                    ocr_text, system_prompt, image_count
                )
            logger.error(f"Error extracting recipe from OCR with Gemini: {str(e)}")
            raise

    # ========================================
    # NEW: Vision API Methods
    # ========================================

    async def extract_recipe_from_images(
        self,
        images: List[bytes],
        context_description: str = "",
        image_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract recipe from images using Gemini Vision API.

        Used for:
        - TikTok slideshows
        - Instagram carousel posts
        - Social media image posts with recipe content

        Args:
            images: List of image bytes
            context_description: Description from the social media post
            image_count: Number of images for stats (defaults to len(images))

        Returns:
            Structured recipe data

        Raises:
            NotARecipeError: If images don't contain a recipe
        """
        if not images:
            raise ValueError("No images provided for Vision API extraction")

        image_count = image_count or len(images)

        try:
            system_prompt = self._get_vision_system_prompt()

            # Build content parts
            content_parts = []

            # Add context if available
            if context_description:
                content_parts.append(
                    f"Post description (may contain recipe details):\n{context_description}\n\n"
                )

            content_parts.append(
                "Analyze the following image(s) to extract a recipe. "
                "The images may contain recipe cards, cooking instructions, "
                "ingredient lists, or step-by-step cooking photos.\n\n"
            )

            # Add images
            for i, img_bytes in enumerate(images):
                # Detect MIME type from magic bytes
                mime_type = self._detect_image_mime_type(img_bytes)
                content_parts.append({
                    "mime_type": mime_type,
                    "data": base64.b64encode(img_bytes).decode("utf-8")
                })
                content_parts.append(f"\n[Image {i + 1} above]\n")

            content_parts.append(
                "\nExtract the recipe and return structured JSON. "
                "Remember to preserve the original language."
            )

            # Get model name based on feature flag
            model_name = await self._get_text_model_name()

            # Create model
            model = self._genai.GenerativeModel(
                model_name=model_name,
                generation_config=self._get_generation_config(),
                system_instruction=system_prompt
            )

            def _generate():
                return model.generate_content(content_parts)

            response = await asyncio.to_thread(_generate)
            result = json.loads(response.text)

            # Check if content is a recipe
            if not result.get("is_recipe", True):
                rejection_reason = result.get("rejection_reason", "Images do not contain a recipe")
                logger.info(f"Vision API: not a recipe - {rejection_reason}")
                raise NotARecipeError(message=rejection_reason)

            # Validate and structure
            normalized = self._validate_and_structure(result)

            # Calculate costs
            # Text tokens
            text_content = system_prompt + context_description
            input_tokens = len(text_content) // 4
            output_tokens = len(response.text) // 4

            # Add image token estimate (~258 tokens per 1000px, assuming 1000x1000 avg)
            image_tokens = image_count * 258
            input_tokens += image_tokens

            normalized["_extraction_stats"] = {
                "model": model_name,
                "provider": "gemini",
                "method": "vision_api",
                "image_count": image_count,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "estimated_cost_usd": self._calculate_cost(input_tokens, output_tokens, model_name)
            }

            logger.info(f"Vision API extracted recipe: {normalized.get('title', 'Unknown')}")
            return normalized

        except NotARecipeError:
            raise
        except Exception as e:
            logger.error(f"Vision API extraction failed: {e}")
            raise

    def _get_vision_system_prompt(self) -> str:
        """Get system prompt for Vision API recipe extraction."""
        return """You are a professional recipe extraction expert with image analysis capabilities.

IMPORTANT - LANGUAGE PRESERVATION:
Extract the recipe in its ORIGINAL language. Do NOT translate.

STEP 1 - IMAGE ANALYSIS:
Analyze the provided images carefully for:
- Recipe cards or printed recipes
- Ingredient lists or nutritional labels
- Step-by-step cooking photos
- Handwritten recipes
- Screenshot of recipes from apps/websites
- Food with visible ingredients

STEP 2 - CONTENT CLASSIFICATION:
Determine if this content is actually a recipe. A recipe must contain:
- Food/dish being prepared (visible or described)
- At least some ingredients OR cooking/preparation instructions

NOT recipes include:
- Random food photos without recipe information
- Restaurant/takeout photos
- Food memes or non-instructional content

STEP 3 - IF RECIPE, EXTRACT DATA:
1. Extract ALL visible ingredients with quantities and units
2. Extract all cooking instructions in order
3. Group ingredients and instructions by recipe sections if applicable
4. If text is partially visible or unclear, make reasonable inferences
5. Return ONLY valid JSON, no markdown

Response format:
{
    "is_recipe": true or false,
    "rejection_reason": "Brief explanation if not a recipe",

    "title": "Recipe name",
    "description": "Brief description",
    "language": "detected language code",
    "ingredients": [
        {"name": "ingredient", "quantity": 2.0, "unit": "cups", "notes": null, "group": null}
    ],
    "instructions": [
        {"step_number": 1, "title": "Step title", "description": "Detailed instruction", "timer_minutes": null, "group": null}
    ],
    "servings": 4,
    "difficulty": "easy|medium|hard",
    "tags": [],
    "categories": [],
    "prep_time_minutes": null,
    "cook_time_minutes": null,
    "resting_time_minutes": null
}"""

    def _detect_image_mime_type(self, image_bytes: bytes) -> str:
        """
        Detect MIME type from image magic bytes.

        Args:
            image_bytes: Raw image bytes

        Returns:
            MIME type string
        """
        if image_bytes[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        elif image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        elif image_bytes[:4] == b"GIF8":
            return "image/gif"
        else:
            # Default to JPEG
            return "image/jpeg"

    # ========================================
    # NEW: Audio Transcription Methods
    # ========================================

    async def transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Gemini 3 Flash.

        Only called when gemini_audio_transcription flag is enabled.

        Args:
            audio_path: Path to audio file (MP3, WAV, etc.)
            prompt: Optional transcription guidance

        Returns:
            Dict with:
                - text: Transcription text
                - duration_seconds: Audio duration
                - tokens: Token count
                - cost: Estimated cost
        """
        try:
            # Read audio file
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            # Get audio duration (rough estimate from file size)
            # MP3: ~128kbps = 16KB/s, WAV: ~176.4KB/s (44.1kHz, 16-bit, stereo)
            file_size = len(audio_bytes)
            is_wav = audio_path.lower().endswith(".wav")
            duration_seconds = file_size / (176400 if is_wav else 16000)

            # Determine MIME type
            mime_type = "audio/wav" if is_wav else "audio/mp3"

            # Build prompt
            transcription_prompt = prompt or "Transcribe this audio accurately. Include all spoken words."

            # Create content parts
            content_parts = [
                transcription_prompt,
                {
                    "mime_type": mime_type,
                    "data": base64.b64encode(audio_bytes).decode("utf-8")
                }
            ]

            # Create model
            model = self._genai.GenerativeModel(
                model_name=self.MODEL_AUDIO,
                generation_config=self._genai.GenerationConfig(
                    temperature=0.1,  # Low temperature for accuracy
                    max_output_tokens=8000
                )
            )

            def _generate():
                return model.generate_content(content_parts)

            response = await asyncio.to_thread(_generate)
            transcript = response.text.strip()

            # Calculate tokens (~25 tokens per second of audio)
            audio_tokens = int(duration_seconds * 25)
            output_tokens = len(transcript) // 4

            # Calculate cost using audio pricing
            pricing = self.PRICING.get("gemini-3-flash-preview-audio", self.PRICING["gemini"])
            cost = (audio_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"]

            logger.info(f"Gemini transcribed {duration_seconds:.1f}s audio, ~${cost:.4f}")

            return {
                "text": transcript,
                "duration_seconds": duration_seconds,
                "input_tokens": audio_tokens,
                "output_tokens": output_tokens,
                "total_tokens": audio_tokens + output_tokens,
                "cost": cost,
                "model": self.MODEL_AUDIO
            }

        except Exception as e:
            logger.error(f"Gemini audio transcription failed: {e}")
            raise

    # ========================================
    # NEW: Image Generation Methods
    # ========================================

    async def generate_recipe_image(
        self,
        recipe_data: Dict[str, Any],
        user_id: str,
        recipe_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate recipe image using Gemini image generation.

        Only called when gemini_image_generation flag is enabled.

        Args:
            recipe_data: Dict containing recipe title, description, etc.
            user_id: UUID of the user
            recipe_id: Optional recipe ID

        Returns:
            Dict with:
                - image_bytes: Raw image bytes
                - cost: Estimated cost
        """
        try:
            title = recipe_data.get("title", "delicious dish")
            description = recipe_data.get("description", "")
            ingredients = recipe_data.get("ingredients", [])
            categories = recipe_data.get("categories", [])

            # Build prompt
            prompt = f"Professional food photography of {title}. "

            if description:
                prompt += f"{description}. "

            # Add key ingredients
            if ingredients:
                ingredient_names = []
                for ing in ingredients[:6]:
                    if isinstance(ing, dict) and "name" in ing:
                        ingredient_names.append(ing["name"])
                if ingredient_names:
                    prompt += f"Key ingredients: {', '.join(ingredient_names)}. "

            if categories:
                prompt += f"{', '.join(categories[:2])} cuisine. "

            prompt += (
                "Beautiful plating, soft natural lighting, shallow depth of field, "
                "appetizing presentation, editorial recipe photography, photorealistic, "
                "high detail, culinary magazine quality."
            )

            # Create model for image generation
            model = self._genai.GenerativeModel(model_name=self.MODEL_IMAGE_GEN)

            def _generate():
                return model.generate_content(
                    prompt,
                    generation_config=self._genai.GenerationConfig(
                        response_modalities=["image", "text"]
                    )
                )

            response = await asyncio.to_thread(_generate)

            # Extract image from response
            image_bytes = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_bytes = part.inline_data.data
                    break

            if not image_bytes:
                raise ValueError("No image generated in response")

            # Calculate cost
            pricing = self.PRICING.get(self.MODEL_IMAGE_GEN, {})
            cost = pricing.get("per_image", 0.039)

            logger.info(f"Gemini generated recipe image for '{title}', ~${cost:.4f}")

            return {
                "image_bytes": image_bytes,
                "cost": cost,
                "model": self.MODEL_IMAGE_GEN
            }

        except Exception as e:
            logger.error(f"Gemini image generation failed: {e}")
            raise
