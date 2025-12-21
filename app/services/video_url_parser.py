"""
Video URL Parser
Parses video URLs from TikTok, YouTube Shorts, Instagram Reels, Facebook, and X/Twitter
to extract platform and video ID for duplicate detection.

Note: X/Twitter support is included but yt-dlp handles it dynamically.
For new platforms, the ContentTypeDetector with yt-dlp probing is preferred.
"""

import re
from urllib.parse import urlparse, urlunparse
from typing import Optional, Set
from dataclasses import dataclass
from enum import Enum


class VideoPlatform(str, Enum):
    """Supported video platforms"""
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"  # Also handles x.com


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
    # Facebook tracking params
    'mibextid',
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
    - Facebook: facebook.com/share/r/ABC, facebook.com/reel/123, facebook.com/watch
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
        VideoPlatform.FACEBOOK: [
            # Facebook Reel share: facebook.com/share/r/CODE
            r'facebook\.com/share/r/([A-Za-z0-9_-]+)',
            # Facebook Reel: facebook.com/reel/CODE
            r'facebook\.com/reel/(\d+)',
            # Facebook video: facebook.com/watch/?v=CODE
            r'facebook\.com/watch/?\?v=(\d+)',
            # Facebook video in user profile: facebook.com/user/videos/CODE
            r'facebook\.com/[^/]+/videos/(\d+)',
        ],
        VideoPlatform.TWITTER: [
            # X.com (Twitter) status URL: x.com/user/status/1234567890
            r'x\.com/[^/]+/status/(\d+)',
            # Twitter.com status URL: twitter.com/user/status/1234567890
            r'twitter\.com/[^/]+/status/(\d+)',
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
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
            return VideoPlatform.FACEBOOK
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return VideoPlatform.TWITTER

        return None

    @classmethod
    def extract_platform_from_url(cls, url: str) -> Optional[str]:
        """
        Extract platform name from URL as a string.

        This is a generic version that returns the platform name string
        instead of the enum, useful for dynamic platform detection.

        Args:
            url: The URL to check

        Returns:
            Platform name string if recognized, None otherwise
        """
        platform = cls.get_platform(url)
        return platform.value if platform else None

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

    @classmethod
    def requires_client_download(cls, url: str) -> bool:
        """
        Check if this platform requires client-side video download.

        Currently only Instagram requires this due to server-side blocking
        (login requirements, rate limiting on datacenter IPs).

        This method is designed to be easily extended to other platforms
        if they start blocking server-side downloads.

        Args:
            url: The video URL to check

        Returns:
            True if the platform requires client-side download
        """
        platform = cls.get_platform(url)
        # Instagram and Facebook require client-side download due to login walls
        return platform in (VideoPlatform.INSTAGRAM, VideoPlatform.FACEBOOK)
