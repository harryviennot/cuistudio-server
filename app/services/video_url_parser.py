"""
Video URL Parser
Parses video URLs from TikTok, YouTube Shorts, and Instagram Reels
to extract platform and video ID for duplicate detection.
"""

import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum


class VideoPlatform(str, Enum):
    """Supported video platforms"""
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"


@dataclass
class ParsedVideoURL:
    """Result of parsing a video URL"""
    platform: VideoPlatform
    video_id: str
    original_url: str
    clean_url: str  # URL with tracking params removed


# Query parameters to strip from URLs (tracking/analytics params)
TRACKING_PARAMS: Set[str] = {
    # TikTok tracking params
    'is_from_webapp',
    'sender_device',
    'web_id',
    '_r',
    '_t',
    'refer',
    'referer',
    'share_source',
    'share_type',
    'share_app_id',
    'share_author_id',
    'share_item_id',
    # Instagram tracking params
    'igsh',
    'igshid',
    'utm_source',
    'utm_medium',
    'utm_campaign',
    # YouTube tracking params
    'si',
    'feature',
    'pp',
    # Common tracking params
    'utm_content',
    'utm_term',
    'fbclid',
    'gclid',
    'ref',
    'source',
}


class VideoURLParser:
    """
    Parse video URLs to extract platform and video ID.

    Supports:
    - TikTok: tiktok.com/@user/video/123, vm.tiktok.com/ABC (short URLs)
    - YouTube Shorts: youtube.com/shorts/ABC, youtu.be/ABC
    - Instagram Reels: instagram.com/reel/ABC, instagram.com/p/ABC
    """

    # URL patterns for each platform
    # Each pattern captures the video ID in group 1
    PATTERNS = {
        VideoPlatform.TIKTOK: [
            # Standard TikTok URL: tiktok.com/@username/video/1234567890
            r'tiktok\.com/@[^/]+/video/(\d+)',
            # Direct video URL: tiktok.com/v/1234567890
            r'tiktok\.com/v/(\d+)',
            # Mobile share URL with video ID in path
            r'tiktok\.com/t/([A-Za-z0-9]+)',
        ],
        VideoPlatform.YOUTUBE: [
            # YouTube Shorts: youtube.com/shorts/VIDEO_ID
            r'youtube\.com/shorts/([A-Za-z0-9_-]{11})',
            # Short URL: youtu.be/VIDEO_ID
            r'youtu\.be/([A-Za-z0-9_-]{11})',
            # Standard YouTube URL with shorts in path
            r'youtube\.com/watch\?v=([A-Za-z0-9_-]{11})',
        ],
        VideoPlatform.INSTAGRAM: [
            # Instagram Reel: instagram.com/reel/CODE
            r'instagram\.com/reel/([A-Za-z0-9_-]+)',
            # Instagram Post (can also be video): instagram.com/p/CODE
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
            # Instagram TV: instagram.com/tv/CODE
            r'instagram\.com/tv/([A-Za-z0-9_-]+)',
        ],
    }

    # Short URL patterns that need to be resolved
    # These URLs redirect to the full URL with video ID
    SHORT_URL_PATTERNS = [
        r'vm\.tiktok\.com/([A-Za-z0-9]+)',  # TikTok short URL
        r'vt\.tiktok\.com/([A-Za-z0-9]+)',  # TikTok short URL variant
    ]

    @classmethod
    def clean_url(cls, url: str) -> str:
        """
        Remove ALL query parameters from video URLs.

        For video platforms, the video ID is always in the URL path,
        never in query params. All query params are tracking/analytics.

        Args:
            url: The URL to clean

        Returns:
            URL with all query parameters removed
        """
        if not url:
            return url

        try:
            parsed = urlparse(url)
            # Remove all query params and fragments for video URLs
            clean_parsed = parsed._replace(query='', fragment='')
            return urlunparse(clean_parsed)
        except Exception:
            # If parsing fails, return original URL
            return url

    @classmethod
    def parse(cls, url: str) -> Optional[ParsedVideoURL]:
        """
        Parse a video URL to extract platform and video ID.

        Args:
            url: The video URL to parse

        Returns:
            ParsedVideoURL if successful, None if URL is not recognized
        """
        if not url:
            return None

        # Normalize URL (lowercase domain, strip trailing slashes)
        normalized_url = url.strip()

        # Try each platform's patterns
        for platform, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, normalized_url, re.IGNORECASE)
                if match:
                    video_id = match.group(1)
                    return ParsedVideoURL(
                        platform=platform,
                        video_id=video_id,
                        original_url=url,
                        clean_url=cls.clean_url(url)
                    )

        return None

    @classmethod
    def is_video_url(cls, url: str) -> bool:
        """
        Check if a URL is a supported video platform URL.

        This includes both direct video URLs and short URLs that redirect
        to video content (like vm.tiktok.com).

        Args:
            url: The URL to check

        Returns:
            True if URL matches a supported video platform
        """
        return cls.parse(url) is not None or cls.is_short_url(url)

    @classmethod
    def is_short_url(cls, url: str) -> bool:
        """
        Check if a URL is a short URL that needs resolution.

        Short URLs (like vm.tiktok.com/ABC) redirect to full URLs.
        These need to be resolved via HTTP redirect to get the actual video ID.

        Args:
            url: The URL to check

        Returns:
            True if URL is a short URL that needs resolution
        """
        if not url:
            return False

        for pattern in cls.SHORT_URL_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        return False

    @classmethod
    def get_platform(cls, url: str) -> Optional[VideoPlatform]:
        """
        Get the platform from a URL without parsing the video ID.

        Args:
            url: The URL to check

        Returns:
            VideoPlatform if recognized, None otherwise
        """
        if not url:
            return None

        url_lower = url.lower()

        if 'tiktok.com' in url_lower:
            return VideoPlatform.TIKTOK
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return VideoPlatform.YOUTUBE
        elif 'instagram.com' in url_lower:
            return VideoPlatform.INSTAGRAM

        return None

    @classmethod
    def normalize_platform_name(cls, platform: str) -> Optional[VideoPlatform]:
        """
        Convert platform string to VideoPlatform enum.

        Args:
            platform: Platform name as string

        Returns:
            VideoPlatform enum value
        """
        platform_lower = platform.lower().strip()
        try:
            return VideoPlatform(platform_lower)
        except ValueError:
            return None
