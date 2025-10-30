"""
Photo extractor using OCR and GPT-4 Vision
"""
import asyncio
import os
import logging
from typing import Dict, Any, List, Union
import pytesseract
from PIL import Image
import io
import tempfile

from app.services.extractors.base_extractor import BaseExtractor
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

# Register HEIF/HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    logger.info("HEIC/HEIF support enabled via pillow-heif")
except ImportError:
    logger.warning("pillow-heif not installed, HEIC images will be converted to JPEG")


class PhotoExtractor(BaseExtractor):
    """Extract recipes from photos (single or multiple images)"""

    def __init__(self, progress_callback=None):
        super().__init__(progress_callback)
        self.openai_service = OpenAIService()

    async def extract(self, source: Union[str, List[str]], **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from photo(s)

        Args:
            source: Photo URL/path or list of photo URLs/paths (max 5)

        Returns:
            Dict containing extracted text and image analysis
        """
        # Handle both single source and multiple sources
        sources = [source] if isinstance(source, str) else source

        if len(sources) == 0:
            raise ValueError("At least one image source is required")

        if len(sources) > 5:
            raise ValueError("Maximum 5 images allowed per extraction")

        try:
            # Process multiple images
            if len(sources) == 1:
                return await self._extract_single_image(sources[0])
            else:
                return await self._extract_multiple_images(sources)

        except Exception as e:
            logger.error(f"Error extracting from photo(s): {str(e)}")
            raise

    async def _extract_single_image(self, source: str) -> Dict[str, Any]:
        """Extract recipe from a single image"""
        self.update_progress(20, "Extracting text from image (OCR)")
        # Run OCR first to get raw text
        # Note: HEIC conversion now happens during upload, not here
        ocr_text = await self._run_ocr(source)

        self.update_progress(50, "Analyzing image and validating with AI")
        # Use GPT-4 Vision to validate OCR and extract structured recipe
        recipe_data = await self.openai_service.extract_recipe_from_image_with_ocr(source, ocr_text)

        self.update_progress(100, "Extraction complete")

        # Add source URL to the recipe data so it can be used as image_url
        recipe_data["source_url"] = source
        recipe_data["source_urls"] = [source]

        # Return the structured recipe data with source URLs
        return recipe_data

    async def _extract_multiple_images(self, sources: List[str]) -> Dict[str, Any]:
        """Extract recipe from multiple images"""
        image_count = len(sources)

        # Step 1: Run OCR on all images
        # Note: HEIC conversion now happens during upload, not here
        all_ocr_texts = []
        for idx, source in enumerate(sources, 1):
            progress = 10 + (40 * idx // image_count)
            self.update_progress(progress, f"Extracting text from image {idx}/{image_count} (OCR)")
            ocr_text = await self._run_ocr(source)
            all_ocr_texts.append(ocr_text)

        # Step 2: Use GPT-4 Vision to analyze all images + OCR together
        self.update_progress(60, f"Analyzing {image_count} images and validating with AI")
        recipe_data = await self.openai_service.extract_recipe_from_images_with_ocr(sources, all_ocr_texts)

        self.update_progress(100, "Multi-image extraction complete")

        # Add source URLs to the recipe data so first image can be used as image_url
        recipe_data["source_url"] = sources[0]  # First image for backward compatibility
        recipe_data["source_urls"] = sources  # All images

        # Return the structured recipe data with source URLs
        return recipe_data

    async def _convert_image_if_needed(self, image_source: str) -> str:
        """
        Convert image to JPEG if it's in an unsupported format (HEIC, etc.)
        Optimized for speed with async downloads and lower quality
        Returns URL or path to converted image
        """
        try:
            # Fast check: if URL ends with supported extension, skip loading
            if image_source.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                return image_source

            # Load image (async for URLs)
            if image_source.startswith('http'):
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_source)
                    image_data = response.content
                image = Image.open(io.BytesIO(image_data))
            else:
                image = Image.open(image_source)

            # Check if conversion is needed
            # OpenAI supports: PNG, JPEG, GIF, WebP
            supported_formats = ['PNG', 'JPEG', 'GIF', 'WEBP']

            if image.format and image.format.upper() in supported_formats:
                # Already in supported format
                return image_source

            # Convert to JPEG
            logger.info(f"Converting {image.format} image to JPEG (async, optimized)")

            # Resize large images BEFORE conversion (huge speedup)
            max_dimension = 2048  # OpenAI max is 2048px
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {image.size} to {new_size}")

            # Convert to RGB if necessary (JPEG doesn't support transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = rgb_image
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Save to temporary file with optimized settings
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                # Quality 85 is sweet spot: 50% smaller, imperceptible quality loss
                # optimize=True enables additional compression
                image.save(tmp_file.name, 'JPEG', quality=85, optimize=True)
                logger.info(f"Saved converted image to {tmp_file.name}")
                return tmp_file.name

        except Exception as e:
            logger.error(f"Error converting image: {str(e)}")
            # Return original if conversion fails
            return image_source

    async def _run_ocr(self, image_source: str) -> str:
        """Run OCR on image with preprocessing for better accuracy"""
        try:
            # Load image (async for URLs)
            if image_source.startswith('http'):
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_source)
                    image_data = response.content
                image = Image.open(io.BytesIO(image_data))
            else:
                image = await asyncio.to_thread(Image.open, image_source)

            # Preprocess image for better OCR (CPU-bound, run in thread pool)
            image = await asyncio.to_thread(self._preprocess_image_for_ocr, image)

            # Run OCR with optimized settings (CPU-bound, run in thread pool)
            # PSM 6 = Assume a single uniform block of text (good for recipe cards)
            custom_config = r'--oem 3 --psm 6'
            text = await asyncio.to_thread(
                pytesseract.image_to_string,
                image,
                config=custom_config
            )

            return text.strip()

        except Exception as e:
            logger.error(f"Error running OCR: {str(e)}")
            return ""

    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy"""
        try:
            from PIL import ImageEnhance, ImageOps
            import numpy as np
            from PIL import ImageFilter

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if image is too large (OCR works best around 300 DPI)
            # Typical recipe card is ~4x6 inches, so 1200x1800 pixels is ideal
            max_dimension = 2400
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Increase contrast for better text recognition
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)

            # Increase sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)

            # Optional: Apply slight denoising
            image = image.filter(ImageFilter.MedianFilter(size=3))

            return image

        except Exception as e:
            logger.warning(f"Error preprocessing image, using original: {str(e)}")
            return image
