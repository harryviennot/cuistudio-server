"""
Voice extractor using Whisper API
"""
import os
import logging
from typing import Dict, Any
from openai import OpenAI

from app.services.extractors.base_extractor import BaseExtractor
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VoiceExtractor(BaseExtractor):
    """Extract recipes from voice recordings"""

    def __init__(self, progress_callback=None):
        super().__init__(progress_callback)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from voice recording

        Args:
            source: Audio file path or URL

        Returns:
            Dict containing transcript
        """
        try:
            self.update_progress(30, "Transcribing audio")

            # Transcribe using OpenAI Whisper API
            transcript = await self._transcribe(source)

            self.update_progress(100, "Transcription complete")

            return {
                "text": transcript,
                "transcript": transcript,
                "source_url": source
            }

        except Exception as e:
            logger.error(f"Error extracting from voice: {str(e)}")
            raise

    async def _transcribe(self, audio_path: str) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )

            return transcript

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise
