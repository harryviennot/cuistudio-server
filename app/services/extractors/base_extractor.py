"""
Base extractor class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for all recipe extractors"""

    def __init__(self, progress_callback: Optional[Callable[[int, str], None]] = None):
        """
        Initialize extractor

        Args:
            progress_callback: Optional callback for progress updates (percentage, step_description)
        """
        self.progress_callback = progress_callback

    def update_progress(self, percentage: int, step: str):
        """Update extraction progress"""
        if self.progress_callback:
            self.progress_callback(percentage, step)
        logger.info(f"Extraction progress: {percentage}% - {step}")

    @abstractmethod
    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from source

        Args:
            source: Source URL or content
            **kwargs: Additional extractor-specific parameters

        Returns:
            Extracted raw content dict with keys like 'text', 'images', etc.
        """
        pass
