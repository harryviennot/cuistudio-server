import os
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


class FluxService:
    """Service for generating recipe images using Flux Pro 1.1 API."""

    BASE_URL = "https://api.bfl.ai/v1"
    FLUX_ENDPOINT = "/flux-pro-1.1"
    MAX_POLL_ATTEMPTS = 60  # 30 seconds max (60 * 0.5s)
    POLL_INTERVAL = 0.5  # seconds
    IMAGE_COST_USD = 0.04

    def __init__(self, supabase_client):
        """Initialize Flux service with Supabase client for image storage.

        Args:
            supabase_client: Supabase client instance for uploading generated images
        """
        self.api_key = os.getenv("BFL_API_KEY")
        self.supabase = supabase_client

        if not self.api_key:
            logger.warning("BFL_API_KEY not set - Flux image generation will be disabled")

    def is_enabled(self) -> bool:
        """Check if Flux service is enabled (API key is set)."""
        return self.api_key is not None

    async def generate_recipe_image(
        self,
        recipe_data: Dict[str, Any],
        user_id: str,
        recipe_id: Optional[str] = None
    ) -> Optional[str]:
        """Generate a recipe book-style image for a recipe.

        Args:
            recipe_data: Dict containing recipe title, description, etc.
            user_id: UUID of the user who created the recipe
            recipe_id: Optional UUID of the recipe (generated if not provided)

        Returns:
            Public URL of the generated image in Supabase Storage, or None if failed
        """
        if not self.is_enabled():
            logger.warning("Flux service disabled - skipping image generation")
            return None

        # Generate unique ID if recipe not saved yet
        if not recipe_id:
            recipe_id = str(uuid.uuid4())

        try:
            logger.info(f"Starting Flux image generation for recipe {recipe_id}")

            # Build prompt from recipe data
            prompt = self._build_prompt(recipe_data)
            logger.debug(f"Generated prompt: {prompt}")

            # Create generation request
            request_data = await self._create_request(prompt)
            if not request_data:
                return None

            polling_url = request_data.get("polling_url")
            request_id = request_data.get("id")
            logger.info(f"Flux request created: {request_id}")

            # Poll for result
            result = await self._poll_result(polling_url)
            if not result:
                return None

            # Get the signed image URL from Flux
            flux_image_url = result.get("result", {}).get("sample")
            if not flux_image_url:
                logger.error("No image URL in Flux result")
                return None

            logger.info(f"Flux image ready: {flux_image_url}")

            # Download and upload to Supabase Storage
            public_url = await self._download_and_upload(
                flux_image_url,
                recipe_id,
                user_id
            )

            if public_url:
                logger.info(f"Image generation successful - Cost: ${self.IMAGE_COST_USD}")
                return public_url

            return None

        except Exception as e:
            logger.error(f"Flux image generation failed: {e}", exc_info=True)
            return None

    def _build_prompt(self, recipe_data: Dict[str, Any]) -> str:
        """Build a detailed recipe book-style prompt from full recipe data.

        Args:
            recipe_data: Dict containing recipe information (title, description, ingredients, etc.)

        Returns:
            Formatted prompt for Flux API with full recipe context
        """
        title = recipe_data.get("title", "delicious dish")
        description = recipe_data.get("description", "")
        ingredients = recipe_data.get("ingredients", [])
        categories = recipe_data.get("categories", [])
        tags = recipe_data.get("tags", [])
        difficulty = recipe_data.get("difficulty", "")

        # Determine food photography style based on recipe attributes
        camera_angle = self._determine_camera_angle(title, categories, tags)
        lighting_style = self._determine_lighting_style(categories, difficulty, tags)
        surface_setting = self._determine_surface_setting(categories, difficulty, tags)
        mood_style = self._determine_mood_style(categories, difficulty, tags)

        # Start with professional food photography structure
        prompt = f"Professional food photography of {title}. "

        # Add description and ingredients as dish context
        if description and len(description) > 10:
            prompt += f"{description}. "

        # Add key ingredients to guide visual representation
        if ingredients and len(ingredients) > 0:
            ingredient_names = []
            for ing in ingredients[:8]:
                if isinstance(ing, dict) and "name" in ing:
                    ingredient_names.append(ing["name"])
                elif isinstance(ing, str):
                    ingredient_names.append(ing.split(",")[0].strip())

            if ingredient_names:
                ingredients_str = ", ".join(ingredient_names[:6])
                prompt += f"Key ingredients visible: {ingredients_str}. "

        # Add cuisine style for cultural context
        if categories:
            category_str = ", ".join(categories[:2])
            prompt += f"{category_str} cuisine. "

        # Add plating and presentation based on difficulty
        if difficulty:
            if difficulty.lower() == "easy":
                prompt += "Styled with rustic, home-style plating on simple dishware. "
            elif difficulty.lower() == "hard":
                prompt += "Styled with refined, sophisticated plating and elegant garnishes. "
            else:
                prompt += "Styled with elegant, appealing plating. "
        else:
            prompt += "Styled with beautiful plating. "

        # Add surface setting
        prompt += f"Placed on {surface_setting}. "

        # Add camera angle
        prompt += f"Shot from {camera_angle}. "

        # Add lighting
        prompt += f"{lighting_style}, shallow depth of field, appetizing presentation. "

        # Add mood/aesthetic
        prompt += f"{mood_style} aesthetic. "

        # Add relevant visual tags
        if tags:
            relevant_tags = [tag for tag in tags[:3] if tag.lower() not in ["easy", "medium", "hard", "quick"]]
            if relevant_tags:
                tags_str = ", ".join(relevant_tags)
                prompt += f"{tags_str}. "

        # Standard quality directives
        prompt += "Editorial recipe photography, photorealistic, high detail, culinary magazine quality"

        return prompt

    def _determine_camera_angle(self, title: str, categories: list, tags: list) -> str:
        """Determine optimal camera angle based on dish type."""
        title_lower = title.lower()
        categories_str = " ".join(categories).lower() if categories else ""
        tags_str = " ".join(tags).lower() if tags else ""
        combined = f"{title_lower} {categories_str} {tags_str}"

        # Overhead for flat/circular dishes
        if any(word in combined for word in ["pizza", "flatbread", "bowl", "salad", "soup", "curry", "ramen", "poke"]):
            return "overhead flat lay angle"
        # Low angle for tall/stacked dishes
        elif any(word in combined for word in ["burger", "sandwich", "stack", "pancake", "layer", "cake"]):
            return "low angle"
        # Straight-on for drinks and layered desserts
        elif any(word in combined for word in ["drink", "cocktail", "smoothie", "parfait", "trifle"]):
            return "straight-on eye level"
        # 45-degree is most versatile for plated dishes
        else:
            return "45-degree angle"

    def _determine_lighting_style(self, categories: list, difficulty: str, tags: list) -> str:
        """Determine lighting style based on dish characteristics."""
        categories_str = " ".join(categories).lower() if categories else ""
        tags_str = " ".join(tags).lower() if tags else ""
        combined = f"{categories_str} {tags_str}"

        # Moody for desserts and steaks
        if any(word in combined for word in ["dessert", "chocolate", "steak", "beef", "indulgent"]):
            return "Moody dramatic lighting with soft shadows"
        # Fresh bright lighting for healthy/fresh dishes
        elif any(word in combined for word in ["fresh", "healthy", "salad", "vegan", "vegetarian", "light"]):
            return "Soft natural window light, bright and fresh"
        # Warm lighting for comfort food
        elif any(word in combined for word in ["comfort", "cozy", "hearty", "warm", "homestyle"]):
            return "Warm golden hour lighting"
        # Elegant lighting for fine dining
        elif difficulty and difficulty.lower() == "hard":
            return "Soft diffused studio lighting, elegant"
        else:
            return "Soft natural window light"

    def _determine_surface_setting(self, categories: list, difficulty: str, tags: list) -> str:
        """Determine surface/background based on cuisine and difficulty."""
        categories_str = " ".join(categories).lower() if categories else ""
        tags_str = " ".join(tags).lower() if tags else ""
        combined = f"{categories_str} {tags_str}"

        # Dark moody for fine dining
        if difficulty and difficulty.lower() == "hard":
            return "dark slate or black marble surface"
        # Rustic for comfort/homestyle
        elif any(word in combined for word in ["rustic", "comfort", "homestyle", "country"]):
            return "rustic wooden table with linen napkin"
        # Clean for healthy/fresh
        elif any(word in combined for word in ["healthy", "fresh", "clean", "light", "vegan"]):
            return "white marble or light wooden surface"
        # Traditional for specific cuisines
        elif any(word in combined for word in ["italian", "french"]):
            return "elegant marble countertop with cloth napkin"
        elif any(word in combined for word in ["asian", "japanese", "chinese"]):
            return "dark wooden table or bamboo mat"
        else:
            return "neutral wooden table"

    def _determine_mood_style(self, categories: list, difficulty: str, tags: list) -> str:
        """Determine overall mood/aesthetic."""
        categories_str = " ".join(categories).lower() if categories else ""
        tags_str = " ".join(tags).lower() if tags else ""
        combined = f"{categories_str} {tags_str}"

        if difficulty and difficulty.lower() == "hard":
            return "Elegant fine dining"
        elif any(word in combined for word in ["comfort", "cozy", "hearty"]):
            return "Cozy comfort food"
        elif any(word in combined for word in ["fresh", "healthy", "light", "vegan"]):
            return "Fresh and vibrant"
        elif any(word in combined for word in ["rustic", "homestyle", "country"]):
            return "Rustic homestyle"
        else:
            return "Clean minimalist"

    async def _create_request(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Create a generation request with Flux API.

        Args:
            prompt: Text prompt for image generation

        Returns:
            Response dict with polling_url and request id, or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}{self.FLUX_ENDPOINT}",
                    headers={
                        "accept": "application/json",
                        "x-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "width": 1024,
                        "height": 1024,
                        "prompt_upsampling": False,
                        "output_format": "jpeg",
                        "safety_tolerance": 2
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Flux API error: {response.status_code} - {response.text}")
                    return None

                return response.json()

        except Exception as e:
            logger.error(f"Failed to create Flux request: {e}", exc_info=True)
            return None

    async def _poll_result(self, polling_url: str) -> Optional[Dict[str, Any]]:
        """Poll Flux API until image is ready.

        Args:
            polling_url: URL to poll for result status

        Returns:
            Result dict with image URL, or None if failed/timeout
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for attempt in range(self.MAX_POLL_ATTEMPTS):
                    await asyncio.sleep(self.POLL_INTERVAL)

                    response = await client.get(
                        polling_url,
                        headers={
                            "accept": "application/json",
                            "x-key": self.api_key
                        }
                    )

                    if response.status_code != 200:
                        logger.error(f"Polling error: {response.status_code} - {response.text}")
                        return None

                    result = response.json()
                    status = result.get("status")

                    logger.debug(f"Flux status: {status} (attempt {attempt + 1}/{self.MAX_POLL_ATTEMPTS})")

                    if status == "Ready":
                        return result
                    elif status in ["Error", "Failed"]:
                        logger.error(f"Flux generation failed: {result}")
                        return None
                    elif status in ["Pending", "Request Moderated"]:
                        continue
                    else:
                        logger.warning(f"Unknown Flux status: {status}")
                        continue

                logger.error(f"Flux polling timeout after {self.MAX_POLL_ATTEMPTS} attempts")
                return None

        except Exception as e:
            logger.error(f"Failed to poll Flux result: {e}", exc_info=True)
            return None

    async def _download_and_upload(
        self,
        flux_image_url: str,
        recipe_id: str,
        user_id: str
    ) -> Optional[str]:
        """Download image from Flux and upload to Supabase Storage.

        Args:
            flux_image_url: Signed URL from Flux API (valid 10 minutes)
            recipe_id: UUID of the recipe
            user_id: UUID of the user

        Returns:
            Public URL in Supabase Storage, or None if failed
        """
        try:
            # Download image from Flux (signed URL expires in 10 minutes)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(flux_image_url)

                if response.status_code != 200:
                    logger.error(f"Failed to download Flux image: {response.status_code}")
                    return None

                image_data = response.content
                logger.info(f"Downloaded image: {len(image_data)} bytes")

            # Generate storage path
            file_name = f"{recipe_id}-generated.jpg"
            storage_path = f"{user_id}/{file_name}"

            # Upload to Supabase Storage
            STORAGE_BUCKET = "recipe-images"

            self.supabase.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=image_data,
                file_options={
                    "content-type": "image/jpeg",
                    "cache-control": "3600",
                    "upsert": "true"
                }
            )

            # Get public URL
            public_url = self.supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
            logger.info(f"Image uploaded to Supabase: {storage_path}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to download/upload image: {e}", exc_info=True)
            return None
