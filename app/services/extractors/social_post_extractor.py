"""
Social Post Extractor for Single Image Posts

Handles extraction from:
- Instagram single image posts
- Facebook posts with recipe images
- Twitter/X posts with recipe content
- Any social media post with a single image and description

Uses a combination of Vision API (for images) and text extraction (for descriptions).
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.services.extractors.base_extractor import BaseExtractor
from app.services.gemini_service import GeminiService
from app.domain.extraction_steps import ExtractionStep

logger = logging.getLogger(__name__)

# Timeout for image download
IMAGE_DOWNLOAD_TIMEOUT = 15.0


class SocialPostExtractor(BaseExtractor):
    """
    Extractor for social media posts with recipe content.

    Handles single image posts where the recipe might be:
    - In the image (recipe card, screenshot)
    - In the description/caption
    - Split between both

    Uses Gemini Vision API when images are available, with fallback
    to text-only extraction from the description.
    """

    def __init__(
        self,
        progress_callback=None,
        gemini_service: Optional[GeminiService] = None,
        cost_tracker=None
    ):
        """
        Initialize SocialPostExtractor.

        Args:
            progress_callback: Optional callback for progress updates
            gemini_service: GeminiService instance for Vision/text extraction
            cost_tracker: Optional CostTrackerService for tracking costs
        """
        super().__init__(progress_callback)
        self._gemini = gemini_service
        self._cost_tracker = cost_tracker

    async def extract(
        self,
        source: str,
        image_urls: Optional[List[str]] = None,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        platform: Optional[str] = None,
        extraction_job_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract recipe from a social media post.

        Strategy:
        1. If images available: Use Vision API with description as context
        2. If only description: Use text extraction

        Args:
            source: Original URL of the post
            image_urls: List of image URLs (usually just one for image posts)
            description: Post description/caption
            thumbnail_url: Fallback thumbnail URL
            platform: Source platform (instagram, facebook, twitter, etc.)
            extraction_job_id: Job ID for cost tracking
            **kwargs: Additional extraction parameters

        Returns:
            Dict containing extracted recipe data

        Raises:
            ValueError: If no content available
            NotARecipeError: If content is not a recipe
        """
        logger.info(f"SocialPostExtractor processing URL: {source}")

        self.update_progress(10, ExtractionStep.SOCIAL_EXTRACTING)

        # Initialize GeminiService if not provided
        if not self._gemini:
            self._gemini = GeminiService()

        # Collect image URLs
        urls_to_process = []
        if image_urls:
            urls_to_process.extend(image_urls)
        elif thumbnail_url:
            urls_to_process.append(thumbnail_url)

        # If we have images, try Vision API extraction
        if urls_to_process:
            result = await self._extract_with_vision(
                urls=urls_to_process,
                description=description,
                extraction_job_id=extraction_job_id
            )
        elif description:
            # No images, try to extract from description only
            result = await self._extract_from_description(
                description=description,
                extraction_job_id=extraction_job_id
            )
        else:
            raise ValueError("No images or description available for extraction")

        self.update_progress(90, ExtractionStep.COMPLETE)

        # Add metadata
        result["source_url"] = source
        result["detected_type"] = "image_post"
        result["platform"] = platform
        result["description"] = description

        # Use first image as recipe image
        if urls_to_process:
            result["image_url"] = urls_to_process[0]

        return result

    async def _extract_with_vision(
        self,
        urls: List[str],
        description: Optional[str],
        extraction_job_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Extract recipe using Vision API with image + description.

        Args:
            urls: Image URLs to download
            description: Post description for context
            extraction_job_id: Job ID for cost tracking

        Returns:
            Extracted recipe data
        """
        self.update_progress(30, ExtractionStep.VISION_ANALYZING)

        # Download images
        images = await self._download_images(urls)

        if not images:
            # Images failed to download, fall back to description
            if description:
                logger.warning("Image download failed, falling back to description extraction")
                return await self._extract_from_description(description, extraction_job_id)
            raise ValueError("Failed to download images and no description available")

        # Extract using Vision API
        result = await self._gemini.extract_recipe_from_images(
            images=images,
            context_description=description or "",
            image_count=len(images)
        )

        # Track cost
        if self._cost_tracker and extraction_job_id:
            stats = result.get("_extraction_stats", {})
            await self._cost_tracker.record_cost(
                extraction_job_id=extraction_job_id,
                service_provider="gemini",
                service_type="vision",
                model_name=stats.get("model", "gemini-3-flash-preview"),
                input_tokens=stats.get("input_tokens"),
                output_tokens=stats.get("output_tokens"),
                images_processed=stats.get("image_count"),
                estimated_cost_usd=stats.get("estimated_cost_usd")
            )

        return result

    async def _extract_from_description(
        self,
        description: str,
        extraction_job_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Extract recipe from post description only.

        Used when images aren't available or fail to download.

        Args:
            description: Post description text
            extraction_job_id: Job ID for cost tracking

        Returns:
            Extracted recipe data
        """
        self.update_progress(50, ExtractionStep.SOCIAL_EXTRACTING)

        # Use normalize_recipe for text-only extraction
        result = await self._gemini.normalize_recipe(
            raw_content=description,
            source_type="social_post"
        )

        # Track cost
        if self._cost_tracker and extraction_job_id:
            stats = result.get("_extraction_stats", {})
            await self._cost_tracker.record_cost(
                extraction_job_id=extraction_job_id,
                service_provider=stats.get("provider", "gemini"),
                service_type="text_extraction",
                model_name=stats.get("model", "gemini-2.5-flash-lite"),
                input_tokens=stats.get("input_tokens"),
                output_tokens=stats.get("output_tokens"),
                estimated_cost_usd=stats.get("estimated_cost_usd")
            )

        return result

    async def _download_images(self, urls: List[str]) -> List[bytes]:
        """
        Download images from URLs concurrently.

        Args:
            urls: List of image URLs

        Returns:
            List of image bytes (excludes failed downloads)
        """
        async def download_one(url: str) -> Optional[bytes]:
            """Download a single image."""
            try:
                async with httpx.AsyncClient(timeout=IMAGE_DOWNLOAD_TIMEOUT) as client:
                    response = await client.get(
                        url,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept': 'image/*,*/*;q=0.8',
                        },
                        follow_redirects=True
                    )
                    response.raise_for_status()

                    # Check content type
                    content_type = response.headers.get("content-type", "")
                    if not content_type.startswith("image/"):
                        logger.warning(f"Non-image content type: {content_type} for {url}")
                        return None

                    return response.content

            except Exception as e:
                logger.warning(f"Failed to download image {url}: {e}")
                return None

        # Download all images concurrently
        tasks = [download_one(url) for url in urls]
        results = await asyncio.gather(*tasks)

        # Filter out failed downloads
        return [img for img in results if img is not None]

    async def extract_from_content_result(
        self,
        content_result,
        extraction_job_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract from a ContentTypeResult object.

        Convenience method for integration with ContentTypeDetector.

        Args:
            content_result: ContentTypeResult from ContentTypeDetector
            extraction_job_id: Job ID for cost tracking
            **kwargs: Additional parameters

        Returns:
            Extracted recipe data
        """
        return await self.extract(
            source=content_result.raw_metadata.get("webpage_url", ""),
            image_urls=content_result.image_urls,
            description=content_result.description,
            thumbnail_url=content_result.thumbnail_url,
            platform=content_result.platform,
            extraction_job_id=extraction_job_id,
            **kwargs
        )
