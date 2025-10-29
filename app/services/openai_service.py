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

    def extract_recipe_from_image_with_ocr(
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
            system_prompt = """You are a professional recipe extraction expert. Your task is to extract structured recipe data from images, using OCR text as a reference that may contain errors.

IMPORTANT RULES:
1. Compare OCR text against the visual image - the image is the ground truth
2. Fix OCR errors: misread characters, merged words, spacing issues
3. Extract COMPLETE ingredients: quantity + unit + name (e.g., "2 cups flour" not "2 cups")
4. Group ingredients logically based on recipe sections:
   - "For the [main dish]" - main ingredients (e.g., "For the soup", "For the duck")
   - "For the [sauce/topping]" - sauce or topping ingredients (e.g., "For the sauce", "For the glaze")
   - "For the garnish" - garnish/decoration ingredients
   - "To taste" - salt, pepper, and seasonings added to preference
   - If no logical groups exist, use null for the group field
5. Number all instruction steps sequentially
6. ESTIMATE cooking time for EACH step based on the action:
   - Prep tasks (chopping, mixing): null
   - "Faites revenir/sauté": 3-5 minutes
   - "Laissez cuire/cook": extract exact time if mentioned, otherwise estimate (10-30 min)
   - "Faites griller/grill": 2-5 minutes
   - "Laissez reposer/rest": extract exact time if mentioned
   - "Mixez/blend": null (instant)
   - Use the TOTAL cook time to validate individual step times add up reasonably
7. If servings not visible, estimate based on ingredient quantities
8. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "title": "Recipe name",
    "description": "Brief description of the dish",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2.0, "unit": "cups", "notes": "optional prep notes", "group": "For the soup"}
    ],
    "instructions": [
        {"step_number": 1, "text": "instruction text", "timer_minutes": 5}
    ],
    "servings": 4,
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"],
    "categories": ["category1"],
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "total_time_minutes": 45
}"""

            user_content = [
                {
                    "type": "text",
                    "text": f"""Extract the recipe from this image. OCR has extracted the following text (may contain errors):

---OCR TEXT---
{ocr_text}
---END OCR---

Task:
1. Validate OCR text against what you see in the image
2. Fix any OCR errors or missing information
3. Extract the COMPLETE recipe with ALL ingredients (quantity + unit + name)
4. Group ingredients if there are logical sections
5. Extract all instruction steps with any timing information
6. Return structured JSON following the specified format"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "detail": "high"
                    }
                }
            ]

            response = self.client.chat.completions.create(
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

            # Validate and structure the response
            normalized = self._validate_and_structure(result)

            # Add usage statistics
            usage = response.usage
            normalized["_extraction_stats"] = {
                "model": "gpt-4o-mini",
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": self._calculate_cost(usage, "gpt-4o-mini")
            }

            logger.info(f"Successfully extracted recipe: {normalized.get('title', 'Unknown')}")
            logger.info(f"Token usage: {usage.total_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

            return normalized

        except Exception as e:
            logger.error(f"Error extracting recipe from image with OCR: {str(e)}")
            raise

    def extract_recipe_from_images_with_ocr(
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
                return self.extract_recipe_from_image_with_ocr(image_urls[0], ocr_texts[0])

            system_prompt = """You are a professional recipe extraction expert. Your task is to extract structured recipe data from multiple images showing different parts of the same recipe.

IMPORTANT RULES:
1. Analyze ALL images together - they show different parts of one recipe
2. Use OCR texts as reference but validate against the images (images are ground truth)
3. Fix OCR errors: misread characters, merged words, spacing issues
4. Extract COMPLETE ingredients from all images: quantity + unit + name
5. Combine ingredients and instructions from all images into one coherent recipe
6. Group ingredients logically based on recipe sections:
   - "For the [main dish]" - main ingredients
   - "For the [sauce/topping]" - sauce or topping ingredients
   - "For the garnish" - garnish/decoration
   - "To taste" - seasonings added to preference
   - Use null if no logical grouping exists
7. Number all instruction steps sequentially across all images
8. ESTIMATE cooking time for EACH step based on the action:
   - Prep tasks (chopping, mixing): null
   - Cooking tasks: extract exact time if mentioned, otherwise estimate based on action
   - Use total cook time to validate individual step times
9. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "title": "Recipe name",
    "description": "Brief description",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2.0, "unit": "cups", "notes": "optional", "group": "For the soup"}
    ],
    "instructions": [
        {"step_number": 1, "text": "instruction text", "timer_minutes": 5}
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

            # Build content with text and all images
            user_content = [
                {
                    "type": "text",
                    "text": f"""Extract the recipe from these {len(image_urls)} images. They show different parts of the same recipe.

OCR has extracted text from each image (may contain errors):

{combined_ocr}

---END OCR---

Task:
1. Analyze all {len(image_urls)} images together
2. Validate OCR texts against what you see in the images
3. Fix any OCR errors or missing information
4. Combine ALL ingredients and instructions from all images
5. Return one complete, structured recipe in JSON format"""
                }
            ]

            # Add all images
            for idx, url in enumerate(image_urls, 1):
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": "high"
                    }
                })

            response = self.client.chat.completions.create(
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

            # Validate and structure
            normalized = self._validate_and_structure(result)

            # Add usage statistics
            usage = response.usage
            normalized["_extraction_stats"] = {
                "model": "gpt-4o-mini",
                "image_count": len(image_urls),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": self._calculate_cost(usage, "gpt-4o-mini")
            }

            logger.info(f"Successfully extracted recipe from {len(image_urls)} images: {normalized.get('title', 'Unknown')}")
            logger.info(f"Token usage: {usage.total_tokens} tokens, ~${normalized['_extraction_stats']['estimated_cost_usd']:.4f}")

            return normalized

        except Exception as e:
            logger.error(f"Error extracting recipe from multiple images: {str(e)}")
            raise

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
