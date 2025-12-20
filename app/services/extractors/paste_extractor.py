"""
Paste extractor for smart copy/paste functionality
"""
import logging
from typing import Dict, Any

from app.services.extractors.base_extractor import BaseExtractor
from app.domain.extraction_steps import ExtractionStep

logger = logging.getLogger(__name__)


class PasteExtractor(BaseExtractor):
    """Extract recipes from pasted text"""

    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from pasted text

        Args:
            source: Pasted recipe text

        Returns:
            Dict containing the text
        """
        try:
            self.update_progress(50, ExtractionStep.PASTE_PROCESSING)

            # For pasted text, we just need to clean it up a bit
            cleaned_text = source.strip()

            self.update_progress(100, ExtractionStep.COMPLETE)

            return {
                "text": cleaned_text,
                "source_url": None
            }

        except Exception as e:
            logger.error(f"Error processing pasted text: {str(e)}")
            raise
