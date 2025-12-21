"""
Slideshow Extractor for Image Carousels

Handles extraction from:
- TikTok photo slideshows (photo mode posts)
- Instagram carousel posts
- Other social media image sequences

Uses Gemini Vision API to extract recipes from multiple images.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx

from app.services.extractors.base_extractor import BaseExtractor
from app.services.gemini_service import GeminiService
from app.domain.extraction_steps import ExtractionStep

logger = logging.getLogger(__name__)

# Maximum images to process (cost control)
MAX_IMAGES = 5

# Timeout for image download
IMAGE_DOWNLOAD_TIMEOUT = 15.0


class SlideshowExtractor(BaseExtractor):
    """
    Extractor for image slideshows/carousels from social media.

    Workflow:
    1. Download images from provided URLs (max 5 for cost control)
    2. Send to Gemini Vision API for recipe extraction
    3. Return structured recipe data
    """

    def __init__(
        self,
        progress_callback=None,
        gemini_service: Optional[GeminiService] = None,
        cost_tracker=None
    ):
        """
        Initialize SlideshowExtractor.

        Args:
            progress_callback: Optional callback for progress updates
            gemini_service: GeminiService instance for Vision API
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
        Extract recipe from slideshow images.

        Args:
            source: Original URL of the slideshow
            image_urls: List of image URLs to download and process
            description: Post description/caption
            thumbnail_url: Fallback thumbnail URL if no image_urls
            platform: Source platform (tiktok, instagram, etc.)
            extraction_job_id: Job ID for cost tracking
            **kwargs: Additional extraction parameters

        Returns:
            Dict containing extracted recipe data

        Raises:
            ValueError: If no images available
            NotARecipeError: If content is not a recipe
        """
        logger.info(f"SlideshowExtractor processing URL: {source}")

        # Collect image URLs
        urls_to_process = []

        if image_urls:
            urls_to_process.extend(image_urls)
        elif thumbnail_url:
            # Fallback to thumbnail if no slideshow images
            urls_to_process.append(thumbnail_url)

        if not urls_to_process:
            raise ValueError("No image URLs provided for slideshow extraction")

        # Limit images for cost control
        if len(urls_to_process) > MAX_IMAGES:
            logger.info(f"Limiting from {len(urls_to_process)} to {MAX_IMAGES} images")
            urls_to_process = urls_to_process[:MAX_IMAGES]

        # Download images
        self.update_progress(10, ExtractionStep.SLIDESHOW_DOWNLOADING)
        images = await self._download_images(urls_to_process)

        if not images:
            raise ValueError("Failed to download any images")

        logger.info(f"Downloaded {len(images)} images for Vision API processing")

        # Initialize GeminiService if not provided
        if not self._gemini:
            self._gemini = GeminiService()

        # Extract recipe using Vision API
        self.update_progress(40, ExtractionStep.SLIDESHOW_ANALYZING)
        result = await self._gemini.extract_recipe_from_images(
            images=images,
            context_description=description or "",
            image_count=len(images)
        )

        # Track cost if tracker available
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

        self.update_progress(90, ExtractionStep.COMPLETE)

        # Add metadata
        result["source_url"] = source
        result["detected_type"] = "slideshow"
        result["platform"] = platform
        result["image_count"] = len(images)
        result["description"] = description

        # Use first image or thumbnail as recipe image
        if urls_to_process:
            result["image_url"] = urls_to_process[0]
        elif thumbnail_url:
            result["image_url"] = thumbnail_url

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
