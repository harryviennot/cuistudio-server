"""
Link extractor for unified URL handling.

Auto-detects whether a URL is from a video platform (TikTok, YouTube, Instagram)
and routes to the appropriate extraction method.
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

logger = logging.getLogger(__name__)

# Default timeout for URL fetching (seconds)
URL_FETCH_TIMEOUT = 30.0


class LinkExtractor(BaseExtractor):
    """
    Unified URL extractor that auto-detects content type.

    For video platform URLs (TikTok, YouTube, Instagram):
        Delegates to VideoExtractor for full video processing.

    For regular webpage URLs:
        Extracts recipe content with image detection.
    """

    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from URL, auto-detecting the type.

        Args:
            source: URL to extract from

        Returns:
            Dict containing extracted content with 'detected_type' field
            indicating whether 'video' or 'url' extraction was used.
        """
        logger.info(f"LinkExtractor processing URL: {source}")

        # Check if it's a video platform URL
        is_video = VideoURLParser.is_video_url(source)
        is_short = VideoURLParser.is_short_url(source)
        logger.info(f"URL detection - is_video: {is_video}, is_short_url: {is_short}")

        if is_video:
            logger.info(f"Detected video URL, delegating to VideoExtractor: {source}")
            return await self._extract_video(source, **kwargs)
        else:
            logger.info(f"Detected webpage URL, extracting content: {source}")
            return await self._extract_webpage(source)

    async def _extract_video(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Delegate to VideoExtractor for video platform URLs.

        Args:
            source: Video URL

        Returns:
            VideoExtractor result with detected_type='video' added
        """
        # Create VideoExtractor with our progress callback
        video_extractor = VideoExtractor(self.progress_callback)

        # Extract video content
        result = await video_extractor.extract(source, **kwargs)

        # Mark the detected type
        result["detected_type"] = "video"

        return result

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
