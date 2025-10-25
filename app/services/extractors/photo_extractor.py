"""
Photo extractor using OCR and GPT-4 Vision
"""
import os
import logging
from typing import Dict, Any
import pytesseract
from PIL import Image

from app.services.extractors.base_extractor import BaseExtractor
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class PhotoExtractor(BaseExtractor):
    """Extract recipes from photos"""

    def __init__(self, progress_callback=None):
        super().__init__(progress_callback)
        self.openai_service = OpenAIService()

    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from photo

        Args:
            source: Photo URL or local path

        Returns:
            Dict containing extracted text and image analysis
        """
        try:
            self.update_progress(20, "Analyzing image with AI")
            # Use GPT-4 Vision to understand the image
            image_description = self.openai_service.enhance_recipe_image_description(source)

            self.update_progress(50, "Extracting text from image (OCR)")
            # Run OCR to extract any text
            ocr_text = await self._run_ocr(source)

            self.update_progress(80, "Combining extracted content")

            # Combine AI analysis and OCR
            combined_text = f"""
AI Image Analysis:
{image_description}

Text Extracted from Image (OCR):
{ocr_text}
"""

            self.update_progress(100, "Extraction complete")

            return {
                "text": combined_text.strip(),
                "image_description": image_description,
                "ocr_text": ocr_text,
                "source_url": source
            }

        except Exception as e:
            logger.error(f"Error extracting from photo: {str(e)}")
            raise

    async def _run_ocr(self, image_source: str) -> str:
        """Run OCR on image"""
        try:
            # Handle both URLs and local paths
            if image_source.startswith('http'):
                import requests
                from io import BytesIO
                response = requests.get(image_source)
                image = Image.open(BytesIO(response.content))
            else:
                image = Image.open(image_source)

            # Run OCR
            text = pytesseract.image_to_string(image)

            return text.strip()

        except Exception as e:
            logger.error(f"Error running OCR: {str(e)}")
            return ""
