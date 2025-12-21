"""
Recipe extraction services for different source types.

Extractors:
- BaseExtractor: Abstract base class for all extractors
- LinkExtractor: Unified URL handler (orchestrator for video/webpage/slideshow/social)
- VideoExtractor: Video transcription (TikTok, YouTube, Instagram, etc.)
- PhotoExtractor: Photo OCR + Vision API
- VoiceExtractor: Voice memo transcription
- PasteExtractor: Pasted text extraction
- SlideshowExtractor: Image carousel extraction (TikTok photo mode, Instagram carousels)
- SocialPostExtractor: Social media image posts
- ContentTypeDetector: Dynamic content type detection using yt-dlp
"""
from app.services.extractors.base_extractor import BaseExtractor
from app.services.extractors.link_extractor import LinkExtractor
from app.services.extractors.video_extractor import VideoExtractor
from app.services.extractors.photo_extractor import PhotoExtractor
from app.services.extractors.voice_extractor import VoiceExtractor
from app.services.extractors.paste_extractor import PasteExtractor
from app.services.extractors.slideshow_extractor import SlideshowExtractor
from app.services.extractors.social_post_extractor import SocialPostExtractor
from app.services.extractors.content_type_detector import ContentTypeDetector, ContentType

__all__ = [
    "BaseExtractor",
    "LinkExtractor",
    "VideoExtractor",
    "PhotoExtractor",
    "VoiceExtractor",
    "PasteExtractor",
    "SlideshowExtractor",
    "SocialPostExtractor",
    "ContentTypeDetector",
    "ContentType",
]
