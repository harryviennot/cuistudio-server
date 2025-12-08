"""
OpenAI service for AI-powered recipe processing
Easily replaceable with other AI providers
"""
from typing import Dict, Any, List, Optional
import json
import logging
import base64
import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIService:
    """Service for OpenAI API interactions"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, organization=settings.OPENAI_ORGANIZATION_ID, project=settings.OPENAI_PROJECT_ID)
        self.model = "gpt-4o"  # Using GPT-4

    async def _download_image_as_base64(self, image_url: str) -> str:
        """
        Download an image from URL and convert to base64 data URI.
        This avoids OpenAI timeout issues when fetching from Supabase storage.

        Args:
            image_url: URL of the image to download

        Returns:
            Base64 data URI string (data:image/jpeg;base64,...)
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()

                # Determine content type from response headers or default to jpeg
                content_type = response.headers.get("content-type", "image/jpeg")
                # Normalize content type (handle cases like "image/jpeg; charset=utf-8")
                content_type = content_type.split(";")[0].strip()

                # Encode to base64
                image_base64 = base64.b64encode(response.content).decode("utf-8")

                logger.debug(f"Downloaded image ({len(response.content)} bytes) as {content_type}")
                return f"data:{content_type};base64,{image_base64}"

        except Exception as e:
            logger.error(f"Error downloading image from {image_url}: {str(e)}")
            raise

    async def normalize_recipe(
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
Your task is to first determine if the content contains a recipe, then extract and structure it.

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
6. Estimate missing timing information based on the recipe
7. Assign appropriate difficulty level (easy, medium, hard)
8. Add relevant tags and categories
9. If servings are not specified, make a reasonable estimate
10. If prep/cook times are not mentioned, estimate based on the recipe complexity
11. DETECT the primary language of the recipe (en for English, fr for French)
12. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "is_recipe": true or false,
    "rejection_reason": "Brief explanation if not a recipe (null if is_recipe=true)",

    // Only include the following fields if is_recipe=true:
    "title": "Recipe name",
    "description": "Brief description",
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

Extract and normalize into JSON format."""

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

            # Check if content is a recipe
            if not result.get("is_recipe", True):
                from app.domain.exceptions import NotARecipeError
                rejection_reason = result.get("rejection_reason", "Content does not appear to be a recipe")
                logger.info(f"Content not a recipe: {rejection_reason}")
                raise NotARecipeError(message=rejection_reason)

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

        # Clean up ingredients: remove whitespace-only units and quantities
        if normalized["ingredients"]:
            for ingredient in normalized["ingredients"]:
                # Convert whitespace-only or empty string units to None
                if "unit" in ingredient:
                    unit = ingredient.get("unit")
                    if isinstance(unit, str) and not unit.strip():
                        ingredient["unit"] = None

                # Convert whitespace-only or empty string quantities to None
                if "quantity" in ingredient:
                    quantity = ingredient.get("quantity")
                    if isinstance(quantity, str) and not quantity.strip():
                        ingredient["quantity"] = None

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

    def enhance_recipe_images_description(self, image_urls: List[str]) -> str:
        """
        Use GPT-4 Vision to describe multiple recipe images together.
        GPT-4o can analyze multiple images in context for better recipe extraction.

        Args:
            image_urls: List of recipe image URLs (max 5)

        Returns:
            Combined description of all images
        """
        try:
            if len(image_urls) == 0:
                return ""

            if len(image_urls) == 1:
                return self.enhance_recipe_image_description(image_urls[0])

            # Build content array with text prompt and all images
            content = [
                {
                    "type": "text",
                    "text": f"""Analyze these {len(image_urls)} recipe images together. They are different views or pages of the same recipe.

Please provide:
1. A comprehensive description of the recipe
2. All visible ingredients from all images
3. All cooking steps shown across the images
4. Any text you can read from any of the images

Combine information from all images to give a complete picture of the recipe."""
                }
            ]

            # Add all images to the content
            for idx, url in enumerate(image_urls, 1):
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": "high"  # Request high detail for better OCR
                    }
                })

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=1500  # More tokens for multiple images
            )

            logger.info(f"Successfully analyzed {len(image_urls)} images together")
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error analyzing multiple images: {str(e)}")
            # Fallback: analyze each image separately
            logger.info("Falling back to individual image analysis")
            descriptions = []
            for idx, url in enumerate(image_urls, 1):
                desc = self.enhance_recipe_image_description(url)
                if desc:
                    descriptions.append(f"Image {idx}:\n{desc}")

            return "\n\n".join(descriptions) if descriptions else ""

    async def extract_recipe_from_image_with_ocr(
        self,
        image_url: str,
        ocr_text: str
    ) -> Dict[str, Any]:
        """
        Extract structured recipe from image using OCR text as reference.
        Uses GPT-4o-mini to validate OCR against visual, fix errors, and structure the recipe.

        Args:
            image_url: URL or path to the recipe image
            ocr_text: Raw OCR text extracted from the image

        Returns:
            Structured recipe data with usage stats
        """
        try:
            system_prompt = """You are a professional recipe extraction expert.

STEP 1 - CONTENT CLASSIFICATION:
Analyze the image to determine what type of content this is:
- "recipe_card": A recipe card, recipe page, or cooking instructions with visible text
- "food_photo": A photo of prepared food/dish (no recipe text visible)
- "non_food": Not food-related content (landscapes, people, pets, objects, etc.)

STEP 2 - EXTRACTION BASED ON TYPE:

If "recipe_card":
- Extract the recipe from the visible text, using OCR as reference
- Compare OCR text against the visual image - the image is the ground truth
- Fix OCR errors: misread characters, merged words, spacing issues

If "food_photo":
- Identify the dish shown in the image
- Generate a plausible, authentic recipe for that dish
- Mark the recipe as AI-generated (is_ai_generated: true)
- Be creative but realistic with ingredients and instructions

If "non_food":
- Return is_recipe: false with a rejection reason

EXTRACTION RULES (for recipe_card and food_photo):
1. Extract COMPLETE ingredients: quantity + unit + name (e.g., "2 cups flour" not "2 cups")
2. Group ingredients logically based on recipe sections:
   - "For the [main dish]" - main ingredients (e.g., "For the soup", "For the duck")
   - "For the [sauce/topping]" - sauce or topping ingredients (e.g., "For the sauce", "For the glaze")
   - "For the garnish" - garnish/decoration ingredients
   - "To taste" - salt, pepper, and seasonings added to preference
   - If no logical groups exist, use null for the group field
3. Number all instruction steps sequentially
4. Each instruction should have a concise title and detailed description
5. Group instructions logically based on recipe sections
6. ESTIMATE cooking time for EACH step based on the action
7. If servings not visible, estimate based on ingredient quantities
8. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "content_type": "recipe_card" | "food_photo" | "non_food",
    "is_recipe": true or false,
    "is_ai_generated": false or true,
    "identified_dish": "Dish name (for food_photo only)",
    "rejection_reason": "Brief explanation (if non_food)",

    // Only include these if is_recipe=true:
    "title": "Recipe name",
    "description": "Brief description of the dish",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2.0, "unit": "cups", "notes": "optional prep notes", "group": "For the soup"}
    ],
    "instructions": [
        {"step_number": 1, "title": "Step title", "description": "Detailed instruction text", "timer_minutes": 5, "group": "For the soup"}
    ],
    "servings": 4,
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"],
    "categories": ["category1"],
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "total_time_minutes": 45
}"""

            # Download image and convert to base64 to avoid OpenAI timeout issues
            # with Supabase storage URLs
            if image_url.startswith("http"):
                logger.info(f"Downloading image for base64 encoding: {image_url[:80]}...")
                image_data_uri = await self._download_image_as_base64(image_url)
            else:
                # Local file path - read and encode
                import aiofiles
                async with aiofiles.open(image_url, "rb") as f:
                    image_bytes = await f.read()
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                image_data_uri = f"data:image/jpeg;base64,{image_base64}"

            user_content = [
                {
                    "type": "text",
                    "text": f"""Analyze this image and extract a recipe. OCR has extracted the following text (may contain errors):

---OCR TEXT---
{ocr_text}
---END OCR---

Task:
1. First, classify the image type (recipe_card, food_photo, or non_food)
2. If recipe_card: Extract the recipe from visible text, fix OCR errors
3. If food_photo: Identify the dish and generate a plausible recipe
4. If non_food: Return is_recipe: false with rejection reason
5. Return structured JSON following the specified format"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_uri,
                        "detail": "high"
                    }
                }
            ]

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )

            result = json.loads(response.choices[0].message.content)

            # Check if content is a recipe
            if not result.get("is_recipe", True):
                from app.domain.exceptions import NotARecipeError
                rejection_reason = result.get("rejection_reason", "Image does not contain a recipe")
                content_type = result.get("content_type", "unknown")
                logger.info(f"Image not a recipe (type: {content_type}): {rejection_reason}")
                raise NotARecipeError(message=rejection_reason)

            # Validate and structure the response
            normalized = self._validate_and_structure(result)

            # Preserve AI-generated flag if present
            if result.get("is_ai_generated"):
                normalized["is_ai_generated"] = True
                normalized["identified_dish"] = result.get("identified_dish")

            # Add usage statistics
            usage = response.usage
            normalized["_extraction_stats"] = {
                "model": "gpt-4o-mini",
                "content_type": result.get("content_type", "recipe_card"),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": self._calculate_cost(usage, "gpt-4o-mini")
            }

            logger.info(f"Successfully extracted recipe: {normalized.get('title', 'Unknown')}")
            if result.get("is_ai_generated"):
                logger.info(f"Recipe was AI-generated from food photo (identified: {result.get('identified_dish')})")
            logger.info(f"Token usage: {usage.total_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

            return normalized

        except Exception as e:
            logger.error(f"Error extracting recipe from image with OCR: {str(e)}")
            raise

    async def extract_recipe_from_images_with_ocr(
        self,
        image_urls: List[str],
        ocr_texts: List[str]
    ) -> Dict[str, Any]:
        """
        Extract structured recipe from multiple images using OCR texts as reference.

        Args:
            image_urls: List of recipe image URLs (max 5)
            ocr_texts: List of OCR texts corresponding to each image

        Returns:
            Structured recipe data with usage stats
        """
        try:
            if len(image_urls) == 0:
                raise ValueError("At least one image is required")

            if len(image_urls) != len(ocr_texts):
                raise ValueError("Number of images must match number of OCR texts")

            if len(image_urls) == 1:
                return await self.extract_recipe_from_image_with_ocr(image_urls[0], ocr_texts[0])

            system_prompt = """You are a professional recipe extraction expert.

STEP 1 - CONTENT CLASSIFICATION:
Analyze all images together to determine what type of content this is:
- "recipe_card": Recipe cards, recipe pages, or cooking instructions with visible text
- "food_photo": Photos of prepared food/dishes (no recipe text visible)
- "non_food": Not food-related content (landscapes, people, pets, objects, etc.)

STEP 2 - EXTRACTION BASED ON TYPE:

If "recipe_card":
- Extract the recipe from the visible text across all images
- Combine ingredients and instructions from all images into one coherent recipe
- Use OCR texts as reference but validate against the images (images are ground truth)
- Fix OCR errors: misread characters, merged words, spacing issues

If "food_photo":
- Identify the dish(es) shown in the images
- Generate a plausible, authentic recipe for that dish
- Mark the recipe as AI-generated (is_ai_generated: true)
- Be creative but realistic with ingredients and instructions

If "non_food":
- Return is_recipe: false with a rejection reason

EXTRACTION RULES (for recipe_card and food_photo):
1. Extract COMPLETE ingredients: quantity + unit + name
2. Group ingredients logically based on recipe sections
3. Number all instruction steps sequentially
4. Each instruction should have a concise title and detailed description
5. Group instructions logically based on recipe sections
6. ESTIMATE cooking time for EACH step based on the action
7. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "content_type": "recipe_card" | "food_photo" | "non_food",
    "is_recipe": true or false,
    "is_ai_generated": false or true,
    "identified_dish": "Dish name (for food_photo only)",
    "rejection_reason": "Brief explanation (if non_food)",

    // Only include these if is_recipe=true:
    "title": "Recipe name",
    "description": "Brief description",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2.0, "unit": "cups", "notes": "optional", "group": "For the soup"}
    ],
    "instructions": [
        {"step_number": 1, "title": "Step title", "description": "Detailed instruction text", "timer_minutes": 5, "group": "For the soup"}
    ],
    "servings": 4,
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"],
    "categories": ["category1"],
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "total_time_minutes": 45
}"""

            # Build OCR text summary
            ocr_summary = []
            for idx, ocr_text in enumerate(ocr_texts, 1):
                ocr_summary.append(f"--- Image {idx} OCR ---\n{ocr_text}")
            combined_ocr = "\n\n".join(ocr_summary)

            # Download all images and convert to base64 to avoid OpenAI timeout issues
            logger.info(f"Downloading {len(image_urls)} images for base64 encoding...")
            image_data_uris = []
            for idx, url in enumerate(image_urls, 1):
                if url.startswith("http"):
                    logger.info(f"Downloading image {idx}/{len(image_urls)}: {url[:60]}...")
                    data_uri = await self._download_image_as_base64(url)
                else:
                    # Local file path - read and encode
                    import aiofiles
                    async with aiofiles.open(url, "rb") as f:
                        image_bytes = await f.read()
                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                    data_uri = f"data:image/jpeg;base64,{image_base64}"
                image_data_uris.append(data_uri)

            # Build content with text and all images
            user_content = [
                {
                    "type": "text",
                    "text": f"""Analyze these {len(image_urls)} images and extract a recipe.

OCR has extracted text from each image (may contain errors):

{combined_ocr}

---END OCR---

Task:
1. First, classify the image type (recipe_card, food_photo, or non_food)
2. If recipe_card: Extract recipe from visible text, fix OCR errors, combine from all images
3. If food_photo: Identify the dish and generate a plausible recipe
4. If non_food: Return is_recipe: false with rejection reason
5. Return structured JSON following the specified format"""
                }
            ]

            # Add all images using base64 data URIs
            for idx, data_uri in enumerate(image_data_uris, 1):
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_uri,
                        "detail": "high"
                    }
                })

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2500  # More tokens for multiple images
            )

            result = json.loads(response.choices[0].message.content)

            # Check if content is a recipe
            if not result.get("is_recipe", True):
                from app.domain.exceptions import NotARecipeError
                rejection_reason = result.get("rejection_reason", "Images do not contain a recipe")
                content_type = result.get("content_type", "unknown")
                logger.info(f"Images not a recipe (type: {content_type}): {rejection_reason}")
                raise NotARecipeError(message=rejection_reason)

            # Validate and structure
            normalized = self._validate_and_structure(result)

            # Preserve AI-generated flag if present
            if result.get("is_ai_generated"):
                normalized["is_ai_generated"] = True
                normalized["identified_dish"] = result.get("identified_dish")

            # Add usage statistics
            usage = response.usage
            normalized["_extraction_stats"] = {
                "model": "gpt-4o-mini",
                "content_type": result.get("content_type", "recipe_card"),
                "image_count": len(image_urls),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": self._calculate_cost(usage, "gpt-4o-mini")
            }

            logger.info(f"Successfully extracted recipe from {len(image_urls)} images: {normalized.get('title', 'Unknown')}")
            if result.get("is_ai_generated"):
                logger.info(f"Recipe was AI-generated from food photo (identified: {result.get('identified_dish')})")
            logger.info(f"Token usage: {usage.total_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

            return normalized

        except Exception as e:
            logger.error(f"Error extracting recipe from multiple images: {str(e)}")
            raise

    async def extract_recipe_from_ocr_text_only(
        self,
        ocr_text: str
    ) -> Dict[str, Any]:
        """
        Extract structured recipe from OCR text only (no image).
        Used for benchmarking to compare against vision-based extraction.

        Args:
            ocr_text: Raw OCR text extracted from the image

        Returns:
            Structured recipe data with usage stats
        """
        try:
            system_prompt = """You are a professional recipe extraction expert.

STEP 1 - CONTENT CLASSIFICATION:
Analyze the OCR text to determine what type of content this is:
- "recipe_card": Recipe text with ingredients and/or instructions
- "non_food": Not food-related content

STEP 2 - EXTRACTION:

If "recipe_card":
- Extract the recipe from the OCR text
- Fix common OCR errors: misread characters (0/O, 1/l/I), merged words, spacing issues
- Structure into proper recipe format

If "non_food":
- Return is_recipe: false with a rejection reason

EXTRACTION RULES (for recipe_card):
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
6. ESTIMATE cooking time for EACH step based on the action
7. If servings not visible, estimate based on ingredient quantities
8. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "content_type": "recipe_card" | "non_food",
    "is_recipe": true or false,
    "rejection_reason": "Brief explanation (if non_food)",

    // Only include these if is_recipe=true:
    "title": "Recipe name",
    "description": "Brief description of the dish",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2.0, "unit": "cups", "notes": "optional prep notes", "group": "For the soup"}
    ],
    "instructions": [
        {"step_number": 1, "title": "Step title", "description": "Detailed instruction text", "timer_minutes": 5, "group": "For the soup"}
    ],
    "servings": 4,
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"],
    "categories": ["category1"],
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "total_time_minutes": 45
}"""

            user_content = f"""Extract a recipe from this OCR text (may contain OCR errors that need fixing):

---OCR TEXT---
{ocr_text}
---END OCR---

Task:
1. First, classify if this is recipe content or not
2. If recipe: Extract and structure the recipe, fixing any OCR errors
3. If not recipe: Return is_recipe: false with rejection reason
4. Return structured JSON following the specified format"""

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )

            result = json.loads(response.choices[0].message.content)

            # Check if content is a recipe
            if not result.get("is_recipe", True):
                from app.domain.exceptions import NotARecipeError
                rejection_reason = result.get("rejection_reason", "Text does not contain a recipe")
                content_type = result.get("content_type", "unknown")
                logger.info(f"OCR text not a recipe (type: {content_type}): {rejection_reason}")
                raise NotARecipeError(message=rejection_reason)

            # Validate and structure the response
            normalized = self._validate_and_structure(result)

            # Add usage statistics
            usage = response.usage
            normalized["_extraction_stats"] = {
                "model": "gpt-4o-mini",
                "method": "ocr_only",
                "content_type": result.get("content_type", "recipe_card"),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": self._calculate_cost_text_only(usage, "gpt-4o-mini")
            }

            logger.info(f"Successfully extracted recipe (OCR-only): {normalized.get('title', 'Unknown')}")
            logger.info(f"Token usage: {usage.total_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

            return normalized

        except Exception as e:
            logger.error(f"Error extracting recipe from OCR text only: {str(e)}")
            raise

    def _calculate_cost_text_only(self, usage, model: str) -> float:
        """Calculate estimated cost for text-only requests (no image tokens)"""
        pricing = {
            "gpt-4o-mini": {
                "input": 0.15,  # per 1M tokens
                "output": 0.60
            },
            "gpt-4o": {
                "input": 2.50,
                "output": 10.00
            }
        }

        if model not in pricing:
            return 0.0

        prices = pricing[model]
        cost = (
            (usage.prompt_tokens / 1_000_000) * prices["input"] +
            (usage.completion_tokens / 1_000_000) * prices["output"]
        )
        return cost

    def _calculate_cost(self, usage, model: str) -> float:
        """Calculate estimated cost based on token usage"""
        # Pricing per 1M tokens (as of Jan 2025)
        pricing = {
            "gpt-4o-mini": {
                "input_text": 0.15,
                "input_image": 2.50,
                "output": 0.60
            },
            "gpt-4o": {
                "input_text": 2.50,
                "input_image": 10.00,
                "output": 10.00
            }
        }

        if model not in pricing:
            return 0.0

        prices = pricing[model]

        # Approximate: assume 80% of input is images, 20% is text for vision calls
        # This is a rough estimate; actual breakdown isn't provided by the API
        input_tokens = usage.prompt_tokens
        image_tokens = int(input_tokens * 0.8)
        text_tokens = input_tokens - image_tokens

        cost = (
            (text_tokens / 1_000_000) * prices["input_text"] +
            (image_tokens / 1_000_000) * prices["input_image"] +
            (usage.completion_tokens / 1_000_000) * prices["output"]
        )

        return cost
