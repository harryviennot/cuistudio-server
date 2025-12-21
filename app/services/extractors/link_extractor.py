"""
Link extractor for unified URL handling.

Auto-detects whether a URL is from a video platform (TikTok, YouTube, Instagram)
and routes to the appropriate extraction method.

Feature Flags:
- dynamic_content_detection: Use ContentTypeDetector instead of hardcoded patterns
- slideshow_extraction: Enable SlideshowExtractor for image carousels
- vision_api_extraction: Enable Vision API for image analysis
- dynamic_client_download: Use PlatformStatusService for dynamic client download detection
"""
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

from app.services.extractors.base_extractor import BaseExtractor
from app.services.extractors.video_extractor import VideoExtractor
from app.services.video_url_parser import VideoURLParser
from app.domain.extraction_steps import ExtractionStep
from app.domain.exceptions import InstagramBlockedError

logger = logging.getLogger(__name__)

# Default timeout for URL fetching (seconds)
URL_FETCH_TIMEOUT = 30.0


class LinkExtractor(BaseExtractor):
    """
    Unified URL extractor that auto-detects content type.

    When dynamic_content_detection flag is DISABLED (default):
        Uses hardcoded VideoURLParser patterns (existing behavior)

    When dynamic_content_detection flag is ENABLED:
        Uses ContentTypeDetector for dynamic detection and routes to:
        - VideoExtractor for videos
        - SlideshowExtractor for image carousels
        - SocialPostExtractor for image posts
        - Webpage scraping for regular sites

    For regular webpage URLs:
        Extracts recipe content with image detection.
    """

    def __init__(
        self,
        progress_callback=None,
        feature_flag_service=None,
        platform_status_service=None,
        gemini_service=None,
        cost_tracker=None,
        skip_duplicate_check: bool = False
    ):
        """
        Initialize LinkExtractor.

        Args:
            progress_callback: Optional callback for progress updates
            feature_flag_service: Optional FeatureFlagService for feature flags
            platform_status_service: Optional PlatformStatusService for dynamic client download
            gemini_service: Optional GeminiService for Vision API
            cost_tracker: Optional CostTrackerService for tracking costs
            skip_duplicate_check: If True, skip duplicate detection (for benchmarking)
        """
        super().__init__(progress_callback)
        self._feature_flags = feature_flag_service
        self._platform_status = platform_status_service
        self._gemini = gemini_service
        self._cost_tracker = cost_tracker
        self._skip_duplicate_check = skip_duplicate_check

    async def extract(
        self,
        source: str,
        extraction_job_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract recipe content from URL, auto-detecting the type.

        Args:
            source: URL to extract from
            extraction_job_id: Optional job ID for cost tracking

        Returns:
            Dict containing extracted content with 'detected_type' field
            indicating whether 'video', 'slideshow', 'image_post', or 'url' extraction was used.
        """
        logger.info(f"LinkExtractor processing URL: {source}")

        # Check if dynamic content detection is enabled
        use_dynamic = await self._is_dynamic_detection_enabled()

        if use_dynamic:
            logger.info("Using dynamic content detection")
            return await self._extract_dynamic(source, extraction_job_id, **kwargs)
        else:
            logger.info("Using legacy content detection")
            return await self._extract_legacy(source, extraction_job_id, **kwargs)

    async def _is_dynamic_detection_enabled(self) -> bool:
        """Check if dynamic content detection feature flag is enabled."""
        if not self._feature_flags:
            return False

        try:
            return await self._feature_flags.is_enabled("dynamic_content_detection")
        except Exception as e:
            logger.warning(f"Failed to check dynamic_content_detection flag: {e}")
            return False

    # ========================================
    # NEW: Dynamic Content Detection Flow
    # ========================================

    async def _extract_dynamic(
        self,
        source: str,
        extraction_job_id: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Dynamic content detection and extraction.

        Uses ContentTypeDetector to probe the URL and route to the appropriate extractor.
        """
        from app.services.extractors.content_type_detector import (
            ContentTypeDetector, ContentType
        )

        detector = ContentTypeDetector()
        content_result = await detector.detect(source)

        logger.info(f"Dynamic detection result: {content_result.content_type.value} for {source}")

        # Route based on content type
        if content_result.content_type == ContentType.VIDEO:
            return await self._extract_video_dynamic(
                source, content_result, extraction_job_id, **kwargs
            )

        elif content_result.content_type == ContentType.SLIDESHOW:
            # Check if slideshow extraction is enabled
            slideshow_enabled = await self._is_feature_enabled("slideshow_extraction")
            if slideshow_enabled:
                try:
                    return await self._extract_slideshow(
                        source, content_result, extraction_job_id, **kwargs
                    )
                except ValueError as e:
                    # No image URLs available - check if this is Instagram
                    if "instagram.com" in source.lower():
                        logger.info(f"Instagram slideshow requires client download: {e}")
                        return {
                            "needs_client_download": True,
                            "platform": "instagram",
                            "content_type": "slideshow",
                            "detected_type": "slideshow",
                            "thumbnail_url": content_result.thumbnail_url,
                            "description": content_result.description,
                            "text": content_result.description or "",
                            "message": "Instagram slideshows require client-side download. Please download the images and upload them."
                        }
                    raise
            else:
                # Fall back to description extraction if available
                if content_result.description:
                    return await self._extract_from_description(
                        source, content_result, extraction_job_id
                    )
                # Otherwise treat as unknown
                logger.warning("Slideshow detected but extraction disabled, falling back")

        elif content_result.content_type == ContentType.IMAGE_POST:
            # Check if vision API extraction is enabled
            vision_enabled = await self._is_feature_enabled("vision_api_extraction")
            if vision_enabled:
                return await self._extract_image_post(
                    source, content_result, extraction_job_id, **kwargs
                )
            else:
                # Fall back to description extraction if available
                if content_result.description:
                    return await self._extract_from_description(
                        source, content_result, extraction_job_id
                    )

        elif content_result.content_type == ContentType.WEBPAGE:
            return await self._extract_webpage(source)

        # UNKNOWN or unsupported - try fallback chain
        return await self._extract_with_fallbacks(
            source, content_result, extraction_job_id, **kwargs
        )

    async def _extract_video_dynamic(
        self,
        source: str,
        content_result,
        extraction_job_id: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Extract video using dynamic platform status checking."""
        # Check if platform requires client download
        needs_client = await self._check_requires_client_download(
            source, content_result.platform
        )

        # Create VideoExtractor with services
        video_extractor = VideoExtractor(
            progress_callback=self.progress_callback,
            feature_flag_service=self._feature_flags,
            gemini_service=self._gemini,
            cost_tracker=self._cost_tracker
        )

        if needs_client:
            logger.info(f"Platform requires client-side download: {content_result.platform}")
            try:
                result = await video_extractor.extract_video_url(source)
                result["detected_type"] = "video"
                result["needs_client_download"] = True
                result["platform"] = content_result.platform
                return result
            except Exception as e:
                # Record failure for dynamic learning
                await self._record_platform_failure(source, content_result.platform, str(e))
                raise

        # Server-side extraction
        try:
            result = await video_extractor.extract(source, extraction_job_id=extraction_job_id, **kwargs)
            result["detected_type"] = "video"
            result["needs_client_download"] = False
            result["platform"] = content_result.platform

            # Record success
            await self._record_platform_success(source, content_result.platform)

            return result
        except Exception as e:
            # Check if this is an auth/rate limit error
            error_msg = str(e).lower()
            if any(term in error_msg for term in ["login", "rate", "blocked", "auth", "403", "401"]):
                # Record failure and potentially mark for client download
                marked = await self._record_platform_failure(source, content_result.platform, error_msg)
                if marked:
                    logger.info(f"Platform {content_result.platform} now requires client download")

                # Try to get URL for client download
                try:
                    result = await video_extractor.extract_video_url(source)
                    result["detected_type"] = "video"
                    result["needs_client_download"] = True
                    result["platform"] = content_result.platform
                    return result
                except Exception:
                    pass

            raise

    async def _extract_slideshow(
        self,
        source: str,
        content_result,
        extraction_job_id: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Extract recipe from slideshow/carousel images."""
        from app.services.extractors.slideshow_extractor import SlideshowExtractor

        extractor = SlideshowExtractor(
            progress_callback=self.progress_callback,
            gemini_service=self._gemini,
            cost_tracker=self._cost_tracker
        )

        return await extractor.extract(
            source=source,
            image_urls=content_result.image_urls,
            description=content_result.description,
            thumbnail_url=content_result.thumbnail_url,
            platform=content_result.platform,
            extraction_job_id=extraction_job_id,
            **kwargs
        )

    async def _extract_image_post(
        self,
        source: str,
        content_result,
        extraction_job_id: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Extract recipe from image post."""
        from app.services.extractors.social_post_extractor import SocialPostExtractor

        extractor = SocialPostExtractor(
            progress_callback=self.progress_callback,
            gemini_service=self._gemini,
            cost_tracker=self._cost_tracker
        )

        return await extractor.extract(
            source=source,
            image_urls=content_result.image_urls,
            description=content_result.description,
            thumbnail_url=content_result.thumbnail_url,
            platform=content_result.platform,
            extraction_job_id=extraction_job_id,
            **kwargs
        )

    async def _extract_from_description(
        self,
        source: str,
        content_result,
        extraction_job_id: Optional[str]
    ) -> Dict[str, Any]:
        """Extract recipe from description text only."""
        from app.services.gemini_service import GeminiService

        gemini = self._gemini or GeminiService(feature_flag_service=self._feature_flags)

        result = await gemini.normalize_recipe(
            raw_content=content_result.description,
            source_type="social_post"
        )

        result["source_url"] = source
        result["detected_type"] = "social_post"
        result["platform"] = content_result.platform
        result["description"] = content_result.description

        if content_result.thumbnail_url:
            result["image_url"] = content_result.thumbnail_url

        return result

    async def _extract_with_fallbacks(
        self,
        source: str,
        content_result,
        extraction_job_id: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fallback chain for unknown content types.

        Tries:
        1. Video extraction if platform is social
        2. Instagram image posts → return needs_client_download
        3. Description extraction if available
        4. Webpage scraping as last resort
        """
        # If it's a social platform, try video extraction
        if content_result.platform:
            try:
                return await self._extract_video_dynamic(
                    source, content_result, extraction_job_id, **kwargs
                )
            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"Video extraction fallback failed: {e}")

                # Check if this is an Instagram image post (no video)
                if "instagram.com/p/" in source.lower() and "no video" in error_msg:
                    logger.info("Instagram image post detected - requires client download")
                    return {
                        "needs_client_download": True,
                        "platform": "instagram",
                        "content_type": "image_post",
                        "detected_type": "image_post",
                        "thumbnail_url": content_result.thumbnail_url,
                        "description": content_result.description,
                        "text": content_result.description or "",
                        "message": "Instagram image posts require client-side download. Please download the images and upload them."
                    }

                # Check if this is a TikTok photo/slideshow (unsupported by yt-dlp)
                if "tiktok.com" in source.lower() and ("unsupported" in error_msg or "/photo/" in source.lower()):
                    logger.info("TikTok photo/slideshow detected - requires client download")
                    return {
                        "needs_client_download": True,
                        "platform": "tiktok",
                        "content_type": "slideshow",
                        "detected_type": "slideshow",
                        "thumbnail_url": content_result.thumbnail_url,
                        "description": content_result.description,
                        "text": content_result.description or "",
                        "message": "TikTok photo slideshows require client-side download. Please download the images and upload them."
                    }

        # Try description extraction
        if content_result.description:
            try:
                return await self._extract_from_description(
                    source, content_result, extraction_job_id
                )
            except Exception as e:
                logger.warning(f"Description extraction fallback failed: {e}")

        # Last resort: webpage scraping
        return await self._extract_webpage(source)

    async def _check_requires_client_download(
        self,
        url: str,
        platform: Optional[str]
    ) -> bool:
        """
        Check if platform requires client-side download.

        Uses dynamic PlatformStatusService if available and feature flag enabled,
        otherwise falls back to static VideoURLParser check.
        """
        # Check if dynamic client download is enabled
        dynamic_enabled = await self._is_feature_enabled("dynamic_client_download")

        if dynamic_enabled and self._platform_status and platform:
            try:
                return await self._platform_status.requires_client_download(platform)
            except Exception as e:
                logger.warning(f"PlatformStatusService check failed: {e}")

        # Fall back to static check
        return VideoURLParser.requires_client_download(url)

    async def _record_platform_failure(
        self,
        url: str,
        platform: Optional[str],
        error: str
    ) -> bool:
        """Record platform failure for dynamic learning."""
        dynamic_enabled = await self._is_feature_enabled("dynamic_client_download")

        if dynamic_enabled and self._platform_status and platform:
            try:
                # Determine failure reason
                error_lower = error.lower()
                if "login" in error_lower or "auth" in error_lower:
                    reason = "auth_required"
                elif "rate" in error_lower:
                    reason = "rate_limited"
                elif "blocked" in error_lower or "403" in error_lower:
                    reason = "blocked"
                else:
                    reason = "unknown"

                return await self._platform_status.record_failure(platform, reason)
            except Exception as e:
                logger.warning(f"Failed to record platform failure: {e}")

        return False

    async def _record_platform_success(
        self,
        url: str,
        platform: Optional[str]
    ) -> None:
        """Record platform success to reset failure count."""
        dynamic_enabled = await self._is_feature_enabled("dynamic_client_download")

        if dynamic_enabled and self._platform_status and platform:
            try:
                await self._platform_status.record_success(platform)
            except Exception as e:
                logger.warning(f"Failed to record platform success: {e}")

    async def _is_feature_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        if not self._feature_flags:
            return False

        try:
            return await self._feature_flags.is_enabled(flag_name)
        except Exception:
            return False

    # ========================================
    # LEGACY: Original Static Detection Flow
    # ========================================

    async def _extract_legacy(
        self,
        source: str,
        extraction_job_id: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Legacy extraction using hardcoded VideoURLParser patterns.

        This is the original behavior when dynamic_content_detection is disabled.
        """
        # Check if it's a video platform URL
        is_video = VideoURLParser.is_video_url(source)
        is_short = VideoURLParser.is_short_url(source)
        logger.info(f"URL detection - is_video: {is_video}, is_short_url: {is_short}")

        if is_video:
            logger.info(f"Detected video URL, delegating to VideoExtractor: {source}")
            return await self._extract_video_legacy(source, extraction_job_id, **kwargs)
        else:
            logger.info(f"Detected webpage URL, extracting content: {source}")
            return await self._extract_webpage(source)

    async def _extract_video_legacy(
        self,
        source: str,
        extraction_job_id: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle video platform URL extraction (legacy mode).

        For platforms requiring client-side download (Instagram):
            Extracts video URL only and signals client to download.

        For other platforms (TikTok, YouTube):
            Full server-side video extraction.
        """
        # Create VideoExtractor with our progress callback
        video_extractor = VideoExtractor(
            progress_callback=self.progress_callback,
            feature_flag_service=self._feature_flags,
            gemini_service=self._gemini,
            cost_tracker=self._cost_tracker
        )

        # Check if this platform requires client-side download (static check)
        if VideoURLParser.requires_client_download(source):
            logger.info(f"Platform requires client-side download: {source}")
            try:
                # Only extract URL and metadata, don't download
                result = await video_extractor.extract_video_url(source)
                result["detected_type"] = "video"
                result["needs_client_download"] = True
                result["platform"] = VideoURLParser.get_platform(source).value
                return result
            except Exception as e:
                # If yt-dlp fails to extract URL, Instagram is blocking us
                error_msg = str(e).lower()
                if "login" in error_msg or "rate" in error_msg or "blocked" in error_msg:
                    raise InstagramBlockedError(
                        url=source,
                        message="Instagram is blocking our access. Please try again later."
                    )
                # Re-raise other errors
                raise

        # For other platforms, use standard full extraction
        result = await video_extractor.extract(source, extraction_job_id=extraction_job_id, **kwargs)
        result["detected_type"] = "video"
        result["needs_client_download"] = False

        return result

    # ========================================
    # WEBPAGE: Traditional Recipe Extraction
    # ========================================

    async def _extract_webpage(self, source: str) -> Dict[str, Any]:
        """
        Extract recipe content from a regular webpage.

        Args:
            source: Webpage URL

        Returns:
            Dict containing text, schema, image_url, and detected_type='url'
        """
        try:
            self.update_progress(10, ExtractionStep.LINK_FETCHING)

            # Fetch the webpage using async httpx with realistic browser headers
            async with httpx.AsyncClient(timeout=URL_FETCH_TIMEOUT) as client:
                response = await client.get(
                    source,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0'
                    },
                    follow_redirects=True
                )

                # Check for 403 Forbidden - website blocks scraping
                if response.status_code == 403:
                    from app.domain.exceptions import WebsiteBlockedError
                    raise WebsiteBlockedError(
                        url=source,
                        message="This website blocks automated recipe extraction"
                    )

                response.raise_for_status()

            self.update_progress(30, ExtractionStep.LINK_PARSING)

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract recipe schema (JSON-LD)
            self.update_progress(50, ExtractionStep.LINK_EXTRACTING)
            recipe_schema = self._extract_schema(soup)

            # Extract image URL
            self.update_progress(60, ExtractionStep.LINK_FINDING_IMAGE)
            image_url = self._extract_image(soup, recipe_schema, source)

            # Extract text content
            self.update_progress(80, ExtractionStep.LINK_EXTRACTING_TEXT)
            text_content = self._extract_text(soup)

            self.update_progress(100, ExtractionStep.COMPLETE)

            # Combine schema and text
            combined_text = ""
            if recipe_schema:
                import json
                combined_text += f"Structured Recipe Data:\n{json.dumps(recipe_schema, indent=2)}\n\n"

            combined_text += f"Page Content:\n{text_content}"

            return {
                "text": combined_text.strip(),
                "schema": recipe_schema,
                "page_text": text_content,
                "source_url": source,
                "image_url": image_url,
                "detected_type": "url"
            }

        except Exception as e:
            logger.error(f"Error extracting from URL: {str(e)}")
            raise

    def _extract_schema(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract recipe from schema.org JSON-LD markup.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Recipe schema dict if found, None otherwise
        """
        try:
            import json

            # Look for JSON-LD schema
            scripts = soup.find_all('script', type='application/ld+json')

            for script in scripts:
                try:
                    if not script.string:
                        continue

                    data = json.loads(script.string)

                    # Handle @graph structure (common in recipe sites)
                    if isinstance(data, dict) and '@graph' in data:
                        for item in data['@graph']:
                            if item.get('@type') == 'Recipe':
                                return item

                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Recipe':
                                return item
                    elif data.get('@type') == 'Recipe':
                        return data

                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error extracting schema: {str(e)}")
            return None

    def _extract_image(
        self,
        soup: BeautifulSoup,
        schema: Optional[Dict[str, Any]],
        base_url: str
    ) -> Optional[str]:
        """
        Extract the main recipe image URL.

        Priority:
        1. JSON-LD Recipe schema 'image' field
        2. Open Graph og:image meta tag
        3. Twitter card image
        4. First large image in content

        Args:
            soup: BeautifulSoup parsed HTML
            schema: Extracted JSON-LD schema (if any)
            base_url: Base URL for resolving relative URLs

        Returns:
            Image URL if found, None otherwise
        """
        try:
            # 1. Try schema.org image
            if schema:
                image = schema.get('image')
                if image:
                    # Image can be a string, list, or ImageObject
                    if isinstance(image, str):
                        return self._resolve_url(image, base_url)
                    elif isinstance(image, list) and len(image) > 0:
                        first_image = image[0]
                        if isinstance(first_image, str):
                            return self._resolve_url(first_image, base_url)
                        elif isinstance(first_image, dict):
                            return self._resolve_url(first_image.get('url', ''), base_url)
                    elif isinstance(image, dict):
                        return self._resolve_url(image.get('url', ''), base_url)

            # 2. Try Open Graph image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return self._resolve_url(og_image['content'], base_url)

            # 3. Try Twitter card image
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                return self._resolve_url(twitter_image['content'], base_url)

            # 4. Try to find a large image in the content
            # Look for images in article, main, or recipe-specific containers
            content_selectors = [
                'article img',
                'main img',
                '.recipe img',
                '.recipe-image img',
                '[itemprop="image"]',
            ]

            for selector in content_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src and self._is_valid_image_url(src):
                        return self._resolve_url(src, base_url)

            return None

        except Exception as e:
            logger.error(f"Error extracting image: {str(e)}")
            return None

    def _resolve_url(self, url: str, base_url: str) -> Optional[str]:
        """Resolve a potentially relative URL to an absolute URL."""
        if not url:
            return None
        if url.startswith('http://') or url.startswith('https://'):
            return url
        return urljoin(base_url, url)

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL looks like a valid image URL (not icons/logos)."""
        if not url:
            return False
        # Skip common non-recipe images
        skip_patterns = ['logo', 'icon', 'avatar', 'profile', 'favicon', 'sprite']
        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in skip_patterns)

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """
        Extract main text content from page.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Cleaned text content
        """
        try:
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ""
