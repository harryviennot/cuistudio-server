"""
Content Type Detector
Uses yt-dlp probing to dynamically detect content type from URLs.

Replaces hardcoded platform patterns with dynamic detection based on actual
content metadata returned by yt-dlp.
"""
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

import yt_dlp

logger = logging.getLogger(__name__)

# Probe timeout in seconds
PROBE_TIMEOUT = 10


class ContentType(str, Enum):
    """Detected content types for extraction routing"""
    VIDEO = "video"           # Standard video with audio
    SLIDESHOW = "slideshow"   # Image carousels (TikTok slideshows, Instagram carousels)
    IMAGE_POST = "image_post" # Single image with description
    WEBPAGE = "webpage"       # Traditional recipe websites (not a social platform)
    UNKNOWN = "unknown"       # Needs fallback handling


@dataclass
class ContentTypeResult:
    """Result of content type detection"""
    content_type: ContentType
    platform: Optional[str] = None  # e.g., "tiktok", "instagram", "youtube"
    video_id: Optional[str] = None

    # Content-specific fields
    image_urls: List[str] = field(default_factory=list)
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = None  # Video duration in seconds

    # Flags
    needs_client_download: bool = False
    has_audio: bool = True

    # Raw metadata for debugging/extension
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


class ContentTypeDetector:
    """
    Detects content type using yt-dlp probing.

    This replaces hardcoded `is_video_url()` patterns with dynamic detection
    based on actual content metadata. Supports:
    - Standard videos (TikTok, YouTube, Instagram Reels, Facebook)
    - Slideshows/carousels (TikTok photo mode, Instagram carousels)
    - Image posts with descriptions
    - Falls back to WEBPAGE for non-social URLs
    """

    # Known social media domains for platform detection
    SOCIAL_DOMAINS = {
        "tiktok.com": "tiktok",
        "vm.tiktok.com": "tiktok",
        "vt.tiktok.com": "tiktok",
        "youtube.com": "youtube",
        "youtu.be": "youtube",
        "instagram.com": "instagram",
        "facebook.com": "facebook",
        "fb.watch": "facebook",
        "x.com": "twitter",
        "twitter.com": "twitter",
    }

    @classmethod
    def extract_domain(cls, url: str) -> str:
        """Extract normalized domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""

    @classmethod
    def get_platform_from_url(cls, url: str) -> Optional[str]:
        """Get platform name from URL domain."""
        domain = cls.extract_domain(url)
        return cls.SOCIAL_DOMAINS.get(domain)

    @classmethod
    def is_social_platform_url(cls, url: str) -> bool:
        """Check if URL is from a known social media platform."""
        return cls.get_platform_from_url(url) is not None

    async def detect(self, url: str) -> ContentTypeResult:
        """
        Detect content type by probing URL with yt-dlp.

        Args:
            url: URL to probe

        Returns:
            ContentTypeResult with detected type and metadata
        """
        # Check if it's a social platform URL first
        platform = self.get_platform_from_url(url)

        if not platform:
            # Not a social platform, treat as webpage
            logger.debug(f"URL is not from a social platform, treating as webpage: {url}")
            return ContentTypeResult(
                content_type=ContentType.WEBPAGE,
                platform=None,
            )

        # Probe with yt-dlp
        try:
            result = await self._probe_with_ytdlp(url, platform)
            logger.info(
                f"Detected content type: {result.content_type.value} "
                f"for platform: {result.platform}, URL: {url}"
            )
            return result
        except Exception as e:
            logger.warning(f"yt-dlp probe failed for {url}: {e}")
            # Return unknown type with platform info for fallback handling
            return ContentTypeResult(
                content_type=ContentType.UNKNOWN,
                platform=platform,
                raw_metadata={"error": str(e)},
            )

    async def _probe_with_ytdlp(self, url: str, platform: str) -> ContentTypeResult:
        """
        Probe URL with yt-dlp to extract metadata without downloading.

        Args:
            url: URL to probe
            platform: Already detected platform name

        Returns:
            ContentTypeResult with detected content type
        """
        def _sync_probe():
            """Synchronous probe - runs in thread pool"""
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': False,  # We want full metadata
                'socket_timeout': PROBE_TIMEOUT,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info

        try:
            # Run with timeout
            info = await asyncio.wait_for(
                asyncio.to_thread(_sync_probe),
                timeout=PROBE_TIMEOUT + 2  # Extra buffer for thread overhead
            )
        except asyncio.TimeoutError:
            logger.warning(f"yt-dlp probe timed out for {url}")
            raise TimeoutError(f"Probe timed out after {PROBE_TIMEOUT}s")

        if not info:
            raise ValueError("yt-dlp returned no info")

        return self._analyze_metadata(info, platform, url)

    def _analyze_metadata(
        self,
        info: Dict[str, Any],
        platform: str,
        url: str
    ) -> ContentTypeResult:
        """
        Analyze yt-dlp metadata to determine content type.

        Detection logic:
        - If 'entries' exists with images → SLIDESHOW
        - If has video formats with duration > 0 → VIDEO
        - If has image formats only → IMAGE_POST
        - Otherwise → UNKNOWN

        Args:
            info: yt-dlp extracted info dict
            platform: Platform name
            url: Original URL

        Returns:
            ContentTypeResult with appropriate type
        """
        # Extract common metadata
        video_id = info.get("id")
        title = info.get("title")
        description = info.get("description", "")
        duration = info.get("duration")
        thumbnail = self._get_best_thumbnail(info)

        # Check for playlist/carousel (TikTok slideshows, Instagram carousels)
        entries = info.get("entries")
        if entries:
            # This is a playlist - check if it's images
            image_urls = self._extract_image_urls_from_entries(entries)
            if image_urls:
                return ContentTypeResult(
                    content_type=ContentType.SLIDESHOW,
                    platform=platform,
                    video_id=video_id,
                    image_urls=image_urls,
                    thumbnail_url=thumbnail,
                    description=description,
                    title=title,
                    duration=None,
                    has_audio=False,
                    raw_metadata=info,
                )

        # Check _type field (yt-dlp uses this for different content types)
        info_type = info.get("_type")

        # Check formats for content type detection
        formats = info.get("formats", [])

        # TikTok slideshow detection: has 'image' type or no video formats
        # TikTok slideshows have extractor = "TikTok" and formats with only images
        is_slideshow = self._is_slideshow(info, formats, platform)
        if is_slideshow:
            image_urls = self._extract_slideshow_images(info, formats)
            return ContentTypeResult(
                content_type=ContentType.SLIDESHOW,
                platform=platform,
                video_id=video_id,
                image_urls=image_urls,
                thumbnail_url=thumbnail,
                description=description,
                title=title,
                duration=None,
                has_audio=self._has_audio_track(info, formats),
                raw_metadata=info,
            )

        # Standard video detection
        if duration and duration > 0:
            return ContentTypeResult(
                content_type=ContentType.VIDEO,
                platform=platform,
                video_id=video_id,
                thumbnail_url=thumbnail,
                description=description,
                title=title,
                duration=duration,
                has_audio=self._has_audio_track(info, formats),
                raw_metadata=info,
            )

        # Check if it's an image post (single image with no video)
        if self._is_image_post(info, formats):
            image_urls = [thumbnail] if thumbnail else []
            return ContentTypeResult(
                content_type=ContentType.IMAGE_POST,
                platform=platform,
                video_id=video_id,
                image_urls=image_urls,
                thumbnail_url=thumbnail,
                description=description,
                title=title,
                has_audio=False,
                raw_metadata=info,
            )

        # Default to VIDEO if we have formats (yt-dlp found something)
        if formats:
            return ContentTypeResult(
                content_type=ContentType.VIDEO,
                platform=platform,
                video_id=video_id,
                thumbnail_url=thumbnail,
                description=description,
                title=title,
                duration=duration,
                has_audio=True,
                raw_metadata=info,
            )

        # Couldn't determine type
        return ContentTypeResult(
            content_type=ContentType.UNKNOWN,
            platform=platform,
            video_id=video_id,
            thumbnail_url=thumbnail,
            description=description,
            title=title,
            raw_metadata=info,
        )

    def _is_slideshow(
        self,
        info: Dict[str, Any],
        formats: List[Dict[str, Any]],
        platform: str
    ) -> bool:
        """
        Detect if content is a slideshow/carousel.

        TikTok slideshows:
        - Have "imagePost" in the data
        - May have formats with only image types
        - Duration is often 0 or very short per image

        Instagram carousels:
        - Have multiple entries
        - _type may be 'playlist'
        """
        # Check for TikTok slideshow indicators
        if platform == "tiktok":
            # Check if all formats are images or if there are image URLs in metadata
            has_video_format = any(
                f.get("vcodec") != "none" and f.get("ext") not in ["jpg", "jpeg", "png", "webp"]
                for f in formats
            )

            # TikTok slideshows often have "imagePost" data or image-only formats
            if not has_video_format and formats:
                return True

            # Check for image_urls in metadata (some yt-dlp versions)
            if info.get("entries") or info.get("_type") == "playlist":
                return True

        # Check for Instagram carousel
        if platform == "instagram":
            if info.get("_type") == "playlist" or info.get("entries"):
                return True

        return False

    def _is_image_post(
        self,
        info: Dict[str, Any],
        formats: List[Dict[str, Any]]
    ) -> bool:
        """Check if content is a single image post."""
        # No video formats, but has thumbnail/image
        has_video = any(
            f.get("vcodec") != "none"
            for f in formats
            if f.get("vcodec")
        )

        has_image = bool(info.get("thumbnail") or info.get("thumbnails"))

        return not has_video and has_image

    def _has_audio_track(
        self,
        info: Dict[str, Any],
        formats: List[Dict[str, Any]]
    ) -> bool:
        """Check if content has audio."""
        # Check for audio-only formats or video formats with audio
        for f in formats:
            acodec = f.get("acodec", "none")
            if acodec and acodec != "none":
                return True

        return info.get("duration", 0) > 0  # Assume videos have audio

    def _extract_image_urls_from_entries(
        self,
        entries: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract image URLs from playlist entries."""
        image_urls = []

        for entry in entries:
            # Try various image URL fields
            url = (
                entry.get("url") or
                entry.get("thumbnail") or
                entry.get("webpage_url")
            )

            if url and self._is_image_url(url):
                image_urls.append(url)

            # Also check thumbnails list
            for thumb in entry.get("thumbnails", []):
                if thumb.get("url"):
                    image_urls.append(thumb["url"])
                    break  # Just get one per entry

        return image_urls

    def _extract_slideshow_images(
        self,
        info: Dict[str, Any],
        formats: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract image URLs from slideshow content."""
        image_urls = []

        # Try formats first (some have direct image URLs)
        for f in formats:
            url = f.get("url")
            ext = f.get("ext", "")

            if url and ext in ["jpg", "jpeg", "png", "webp"]:
                image_urls.append(url)

        # Try thumbnails if no images in formats
        if not image_urls:
            for thumb in info.get("thumbnails", []):
                if thumb.get("url"):
                    image_urls.append(thumb["url"])

        # Try entries (carousels)
        entries = info.get("entries", [])
        for entry in entries:
            entry_images = self._extract_image_urls_from_entries([entry])
            image_urls.extend(entry_images)

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for url in image_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def _is_image_url(self, url: str) -> bool:
        """Check if URL looks like an image URL."""
        if not url:
            return False

        url_lower = url.lower()
        image_extensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"]

        return any(url_lower.endswith(ext) or ext + "?" in url_lower for ext in image_extensions)

    def _get_best_thumbnail(self, info: Dict[str, Any]) -> Optional[str]:
        """Get the best thumbnail URL from metadata."""
        thumbnails = info.get("thumbnails", [])

        # Build lookup by id
        thumb_by_id = {t.get("id"): t.get("url") for t in thumbnails if t.get("url")}

        # Prefer specific IDs (platform-dependent)
        for preferred_id in ["cover", "originCover", "0", "default"]:
            if preferred_id in thumb_by_id:
                return thumb_by_id[preferred_id]

        # Fall back to default thumbnail field
        if info.get("thumbnail"):
            return info["thumbnail"]

        # Return first available thumbnail
        if thumbnails and thumbnails[0].get("url"):
            return thumbnails[0]["url"]

        return None
