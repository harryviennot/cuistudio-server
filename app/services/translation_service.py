"""
Translation Service

Provides localized strings for notifications and other server-side content.
Loads translations from JSON files and supports variable interpolation.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Supported languages
SUPPORTED_LANGUAGES = ("en", "fr")
DEFAULT_LANGUAGE = "en"

# Cache for loaded translations
_translations_cache: Dict[str, Dict[str, Any]] = {}


def _get_translations_dir() -> Path:
    """Get the path to the translations directory."""
    return Path(__file__).parent.parent / "translations"


def _load_translations(language: str) -> Dict[str, Any]:
    """
    Load translations for a specific language.

    Results are cached for performance.
    """
    if language in _translations_cache:
        return _translations_cache[language]

    translations_file = _get_translations_dir() / f"{language}.json"

    try:
        with open(translations_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
            _translations_cache[language] = translations
            logger.info(f"Loaded translations for language: {language}")
            return translations
    except FileNotFoundError:
        logger.warning(f"Translation file not found for language: {language}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in translation file for {language}: {e}")
        return {}


def _get_nested_value(data: Dict[str, Any], key: str) -> Optional[str]:
    """
    Get a nested value from a dictionary using dot notation.

    Example: _get_nested_value(data, "notifications.welcome.title")
    """
    keys = key.split(".")
    value = data

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None

    return value if isinstance(value, str) else None


class TranslationService:
    """Service for retrieving localized strings."""

    def __init__(self):
        # Pre-load all supported languages
        for lang in SUPPORTED_LANGUAGES:
            _load_translations(lang)

    def translate(
        self,
        key: str,
        language: str = DEFAULT_LANGUAGE,
        **params: Any
    ) -> str:
        """
        Get a translated string by key with variable interpolation.

        Args:
            key: Dot-notation key (e.g., "notifications.welcome.title")
            language: Target language code (e.g., "en", "fr")
            **params: Variables to interpolate into the string

        Returns:
            Translated string with variables substituted, or the key if not found.

        Example:
            translate("notifications.credits.body", "fr", credits=5)
            # Returns: "Vous avez 5 extractions gratuites cette semaine."
        """
        # Validate language, fallback to default
        if language not in SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language '{language}', falling back to {DEFAULT_LANGUAGE}")
            language = DEFAULT_LANGUAGE

        translations = _load_translations(language)
        value = _get_nested_value(translations, key)

        # Fallback to English if key not found in target language
        if value is None and language != DEFAULT_LANGUAGE:
            logger.debug(f"Key '{key}' not found in {language}, falling back to {DEFAULT_LANGUAGE}")
            translations = _load_translations(DEFAULT_LANGUAGE)
            value = _get_nested_value(translations, key)

        # If still not found, return the key itself
        if value is None:
            logger.warning(f"Translation key not found: {key}")
            return key

        # Interpolate variables
        try:
            return value.format(**params)
        except KeyError as e:
            logger.error(f"Missing interpolation variable for key '{key}': {e}")
            return value

    def get_notification_text(
        self,
        notification_type: str,
        language: str = DEFAULT_LANGUAGE,
        **params: Any
    ) -> tuple[str, str]:
        """
        Get title and body for a notification type.

        Args:
            notification_type: The notification type (e.g., "weekly_credits_refresh")
            language: Target language code
            **params: Variables to interpolate

        Returns:
            Tuple of (title, body)
        """
        title = self.translate(
            f"notifications.{notification_type}.title",
            language,
            **params
        )
        body = self.translate(
            f"notifications.{notification_type}.body",
            language,
            **params
        )
        return title, body

    def is_supported_language(self, language: str) -> bool:
        """Check if a language is supported."""
        return language in SUPPORTED_LANGUAGES


# Singleton instance for convenience
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Get the singleton TranslationService instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service
