"""
Extraction step codes for progress tracking.
These are typed codes that the frontend maps to localized strings.
"""
from enum import Enum


class ExtractionStep(str, Enum):
    """
    Typed extraction step codes.

    Frontend maps these to translations via i18n:
    t(`extraction.steps.${step}`)
    """

    # General steps
    STARTING = "starting"
    COMPLETE = "complete"

    # Video extraction (0-50% range in extraction phase)
    VIDEO_DOWNLOADING = "video_downloading"
    VIDEO_EXTRACTING_AUDIO = "video_extracting_audio"
    VIDEO_TRANSCRIBING = "video_transcribing"
    VIDEO_COMBINING = "video_combining"
    GEMINI_TRANSCRIBING = "gemini_transcribing"  # Gemini audio transcription (alternative to Whisper)

    # Slideshow extraction (for TikTok photo mode, Instagram carousels)
    SLIDESHOW_DOWNLOADING = "slideshow_downloading"
    SLIDESHOW_ANALYZING = "slideshow_analyzing"

    # Social post extraction (image posts with descriptions)
    SOCIAL_EXTRACTING = "social_extracting"
    VISION_ANALYZING = "vision_analyzing"

    # Photo extraction
    PHOTO_OCR_SINGLE = "photo_ocr_single"
    PHOTO_OCR_MULTIPLE = "photo_ocr_multiple"
    PHOTO_EXTRACTING = "photo_extracting"

    # Voice extraction
    VOICE_TRANSCRIBING = "voice_transcribing"

    # Link extraction
    LINK_FETCHING = "link_fetching"
    LINK_PARSING = "link_parsing"
    LINK_EXTRACTING = "link_extracting"
    LINK_FINDING_IMAGE = "link_finding_image"
    LINK_EXTRACTING_TEXT = "link_extracting_text"

    # Paste extraction
    PASTE_PROCESSING = "paste_processing"

    # Normalization phase (50-100% range)
    NORMALIZING = "normalizing"
    PREPARING = "preparing"
    GENERATING_IMAGE = "generating_image"
    SAVING = "saving"
