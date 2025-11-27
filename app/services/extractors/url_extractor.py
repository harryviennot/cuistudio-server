"""
URL extractor for web scraping recipe websites
"""
import logging
from typing import Dict, Any
import httpx
from bs4 import BeautifulSoup

from app.services.extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

# Default timeout for URL fetching (seconds)
URL_FETCH_TIMEOUT = 30.0


class URLExtractor(BaseExtractor):
    """Extract recipes from URLs using web scraping"""

    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from URL

        Args:
            source: Recipe website URL

        Returns:
            Dict containing extracted content
        """
        try:
            self.update_progress(20, "Fetching webpage")

            # Fetch the webpage using async httpx
            async with httpx.AsyncClient(timeout=URL_FETCH_TIMEOUT) as client:
                response = await client.get(
                    source,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    },
                    follow_redirects=True
                )
                response.raise_for_status()

            self.update_progress(50, "Parsing HTML content")

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Try to find recipe schema (recipe websites often use schema.org)
            recipe_schema = await self._extract_schema(soup)

            self.update_progress(70, "Extracting recipe text")

            # Extract text content
            text_content = await self._extract_text(soup)

            self.update_progress(100, "Extraction complete")

            # Combine schema and text
            combined_text = ""
            if recipe_schema:
                combined_text += f"Structured Recipe Data:\n{recipe_schema}\n\n"

            combined_text += f"Page Content:\n{text_content}"

            return {
                "text": combined_text.strip(),
                "schema": recipe_schema,
                "page_text": text_content,
                "source_url": source
            }

        except Exception as e:
            logger.error(f"Error extracting from URL: {str(e)}")
            raise

    async def _extract_schema(self, soup: BeautifulSoup) -> str:
        """Try to extract recipe from schema.org markup"""
        try:
            import json

            # Look for JSON-LD schema
            scripts = soup.find_all('script', type='application/ld+json')

            for script in scripts:
                try:
                    data = json.loads(script.string)

                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Recipe':
                                return json.dumps(item, indent=2)
                    elif data.get('@type') == 'Recipe':
                        return json.dumps(data, indent=2)

                except json.JSONDecodeError:
                    continue

            return ""

        except Exception as e:
            logger.error(f"Error extracting schema: {str(e)}")
            return ""

    async def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content from page"""
        try:
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

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
