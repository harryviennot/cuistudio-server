"""
Video extractor for TikTok, Reels, YouTube Shorts

Simplified extraction flow:
1. Download video with yt-dlp (get metadata + thumbnail URL)
2. Extract audio with MoviePy
3. Transcribe audio with Whisper (or Gemini if feature flag enabled)
4. Return transcript + description (no frame OCR)

NOTE: All blocking operations (yt-dlp, whisper, moviepy)
are wrapped in asyncio.to_thread() to prevent blocking the event loop.
This allows SSE progress events to be sent in real-time.

Feature Flags:
- gemini_audio_transcription: Use Gemini 3 Flash for audio transcription instead of Whisper
"""
import os
import logging
import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List, Optional

import yt_dlp
import whisper
from moviepy.video.io.VideoFileClip import VideoFileClip

from app.services.extractors.base_extractor import BaseExtractor
from app.core.config import get_settings
from app.domain.extraction_steps import ExtractionStep

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def get_whisper_model(model_name: str = "base"):
    """
    Load and cache Whisper model. Only loaded once per process.

    Args:
        model_name: Model size - tiny, base, small, medium, large

    Returns:
        Loaded Whisper model
    """
    logger.info(f"Loading Whisper model: {model_name}")
    return whisper.load_model(model_name)


class VideoExtractor(BaseExtractor):
    """Extract recipes from video URLs (TikTok, Reels, Shorts)"""

    def __init__(
        self,
        progress_callback=None,
        feature_flag_service=None,
        gemini_service=None,
        cost_tracker=None
    ):
        """
        Initialize VideoExtractor.

        Args:
            progress_callback: Optional callback for progress updates
            feature_flag_service: Optional FeatureFlagService for transcription method selection
            gemini_service: Optional GeminiService for Gemini audio transcription
            cost_tracker: Optional CostTrackerService for tracking costs
        """
        super().__init__(progress_callback)
        self.download_dir = "temp/videos"
        os.makedirs(self.download_dir, exist_ok=True)
        # Track temp files for cleanup
        self._temp_files: List[Path] = []
        # Feature flag and services for Gemini transcription
        self._feature_flags = feature_flag_service
        self._gemini = gemini_service
        self._cost_tracker = cost_tracker
        # Track extraction job ID for cost tracking
        self._current_job_id: Optional[str] = None

    def _get_best_thumbnail(self, info: dict) -> Optional[str]:
        """Get the best thumbnail URL, preferring creator-selected cover."""
        thumbnails = info.get("thumbnails", [])

        # Build lookup by id
        thumb_by_id = {t.get("id"): t.get("url") for t in thumbnails}

        # Prefer 'cover' (creator-selected), fallback to 'originCover', then default
        return (
            thumb_by_id.get("cover")
            or thumb_by_id.get("originCover")
            or info.get("thumbnail")
        )

    def _track_temp_file(self, path: str) -> str:
        """Track a temp file for cleanup after extraction."""
        self._temp_files.append(Path(path))
        return path

    def _cleanup_temp_files(self):
        """Remove all tracked temp files."""
        for file_path in self._temp_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

        self._temp_files.clear()
        logger.info("Temp file cleanup completed")

    async def extract(self, source: str, extraction_job_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from video URL.

        Simplified flow (no frame OCR):
        1. Download video and get metadata
        2. Extract and transcribe audio
        3. Combine transcript with video description

        Args:
            source: Video URL (TikTok, Instagram, YouTube)
            extraction_job_id: Optional job ID for cost tracking

        Returns:
            Dict containing transcript, description, video metadata, and thumbnail URL
        """
        self._current_job_id = extraction_job_id

        try:
            self.update_progress(5, ExtractionStep.VIDEO_DOWNLOADING)
            video_path, video_metadata = await self._download_video(source)
            self._track_temp_file(video_path)

            description = video_metadata.get("description", "")

            self.update_progress(30, ExtractionStep.VIDEO_EXTRACTING_AUDIO)
            audio_path = await self._extract_audio(video_path)
            self._track_temp_file(audio_path)

            # Check feature flag for transcription method
            use_gemini = await self._should_use_gemini_transcription()
            if use_gemini:
                self.update_progress(50, ExtractionStep.GEMINI_TRANSCRIBING)
                transcript = await self._transcribe_audio_gemini(audio_path)
            else:
                self.update_progress(50, ExtractionStep.VIDEO_TRANSCRIBING)
                transcript = await self._transcribe_audio_whisper(audio_path)

            self.update_progress(90, ExtractionStep.VIDEO_COMBINING)

            # Combine transcript and description (no OCR text)
            combined_text = f"""Video Description: {description}

Transcript:
{transcript}"""

            self.update_progress(100, ExtractionStep.COMPLETE)

            return {
                "text": combined_text.strip(),
                "transcript": transcript,
                "description": description,
                "video_path": video_path,
                "source_url": source,
                # Video metadata from yt-dlp
                "video_title": video_metadata.get("title"),
                "thumbnail_url": video_metadata.get("thumbnail"),
                "webpage_url": video_metadata.get("webpage_url"),
                "duration": video_metadata.get("duration"),
                "view_count": video_metadata.get("view_count"),
                "like_count": video_metadata.get("like_count"),
                "upload_date": video_metadata.get("upload_date"),
                # Creator info
                "uploader": video_metadata.get("uploader"),
                "uploader_id": video_metadata.get("uploader_id"),
                "channel": video_metadata.get("channel"),
                "channel_id": video_metadata.get("channel_id"),
                "channel_url": video_metadata.get("channel_url"),
                # Store raw metadata for future use
                "raw_metadata": video_metadata
            }

        except Exception as e:
            logger.error(f"Error extracting from video: {str(e)}")
            raise
        finally:
            # Always cleanup temp files, even on error
            self._cleanup_temp_files()

    async def _download_video(self, url: str) -> tuple[str, Dict[str, Any]]:
        """
        Download video using yt-dlp and extract full metadata.

        Args:
            url: Video URL to download

        Returns:
            Tuple of (video_path, metadata_dict)
        """
        download_dir = self.download_dir

        def _sync_download():
            """Synchronous download - runs in thread pool"""
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'{download_dir}/%(id)s.%(ext)s',
                'quiet': True,
                'writethumbnail': False,  # We'll use the URL instead
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)

                # Extract comprehensive metadata
                metadata = {
                    # Basic info
                    "id": info.get("id"),
                    "title": info.get("title"),
                    "description": info.get("description", ""),

                    # URLs
                    "webpage_url": info.get("webpage_url"),
                    "thumbnail": self._get_best_thumbnail(info),

                    # Video stats
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                    "comment_count": info.get("comment_count"),

                    # Dates
                    "upload_date": info.get("upload_date"),  # Format: YYYYMMDD
                    "timestamp": info.get("timestamp"),

                    # Creator/Channel info
                    "uploader": info.get("uploader"),
                    "uploader_id": info.get("uploader_id"),
                    "uploader_url": info.get("uploader_url"),
                    "channel": info.get("channel"),
                    "channel_id": info.get("channel_id"),
                    "channel_url": info.get("channel_url"),
                    "channel_follower_count": info.get("channel_follower_count"),

                    # Platform-specific
                    "extractor": info.get("extractor"),  # e.g., "TikTok", "youtube"
                    "extractor_key": info.get("extractor_key"),

                    # Tags and categories
                    "tags": info.get("tags", []),
                    "categories": info.get("categories", []),

                    # Technical info
                    "ext": info.get("ext"),
                    "width": info.get("width"),
                    "height": info.get("height"),
                    "fps": info.get("fps"),
                }

                logger.info(
                    f"Downloaded video: {metadata.get('title', 'Unknown')} "
                    f"from {metadata.get('extractor', 'unknown')} "
                    f"by {metadata.get('uploader', 'unknown')}"
                )

                return video_path, metadata

        try:
            return await asyncio.to_thread(_sync_download)
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise

    async def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video."""
        def _sync_extract():
            """Synchronous audio extraction - runs in thread pool"""
            audio_path = video_path.replace(os.path.splitext(video_path)[1], '.mp3')
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path, logger=None)
            video.close()
            return audio_path

        try:
            return await asyncio.to_thread(_sync_extract)
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise

    async def _should_use_gemini_transcription(self) -> bool:
        """
        Check if Gemini transcription should be used based on feature flag.

        Returns:
            True if Gemini transcription is enabled and available
        """
        if not self._feature_flags:
            return False

        try:
            return await self._feature_flags.is_enabled("gemini_audio_transcription")
        except Exception as e:
            logger.warning(f"Failed to check feature flag: {e}")
            return False

    async def _transcribe_audio_whisper(self, audio_path: str) -> str:
        """
        Transcribe audio using OpenAI Whisper with cached model.

        This is the original/default transcription method.
        """
        def _sync_transcribe():
            """Synchronous transcription - runs in thread pool (CPU-intensive)"""
            # Use cached Whisper model (loaded once per process)
            model = get_whisper_model(settings.WHISPER_MODEL)
            # Transcribe
            result = model.transcribe(audio_path)
            return result["text"]

        try:
            transcript = await asyncio.to_thread(_sync_transcribe)

            # Track cost (Whisper is free when run locally)
            if self._cost_tracker and self._current_job_id:
                await self._cost_tracker.record_cost(
                    extraction_job_id=self._current_job_id,
                    service_provider="whisper_local",
                    service_type="transcription",
                    model_name=settings.WHISPER_MODEL,
                    estimated_cost_usd=0.0  # Local Whisper is free
                )

            return transcript
        except Exception as e:
            logger.error(f"Error transcribing audio with Whisper: {str(e)}")
            return ""

    async def _transcribe_audio_gemini(self, audio_path: str) -> str:
        """
        Transcribe audio using Gemini 3 Flash.

        Used when gemini_audio_transcription feature flag is enabled.
        """
        try:
            # Initialize GeminiService if not provided
            if not self._gemini:
                from app.services.gemini_service import GeminiService
                self._gemini = GeminiService(feature_flag_service=self._feature_flags)

            # Transcribe using Gemini
            result = await self._gemini.transcribe_audio(
                audio_path=audio_path,
                prompt="Transcribe this audio accurately. Include all spoken words."
            )

            transcript = result.get("text", "")

            # Track cost
            if self._cost_tracker and self._current_job_id:
                await self._cost_tracker.record_cost(
                    extraction_job_id=self._current_job_id,
                    service_provider="gemini",
                    service_type="transcription",
                    model_name=result.get("model", "gemini-3-flash-preview"),
                    input_tokens=result.get("input_tokens"),
                    output_tokens=result.get("output_tokens"),
                    audio_seconds=result.get("duration_seconds"),
                    estimated_cost_usd=result.get("cost")
                )

            logger.info(f"Gemini transcription completed: {len(transcript)} chars")
            return transcript

        except Exception as e:
            logger.error(f"Error transcribing audio with Gemini: {str(e)}")
            # Fall back to Whisper on Gemini failure
            logger.info("Falling back to Whisper transcription")
            return await self._transcribe_audio_whisper(audio_path)

    async def extract_video_url(self, url: str) -> Dict[str, Any]:
        """
        Extract direct video URL and metadata WITHOUT downloading.

        Used for platforms requiring client-side download (e.g., Instagram).
        The server extracts the direct MP4 URL using yt-dlp, and the client
        downloads the video using their own IP to bypass platform blocking.

        Args:
            url: Video URL (Instagram reel, etc.)

        Returns:
            Dict containing:
                - video_url: Direct MP4 URL for client to download
                - thumbnail_url: Thumbnail image URL
                - description: Video description
                - platform: Platform name
                - Other metadata (title, duration, uploader, etc.)
        """
        def _sync_extract_info():
            """Synchronous info extraction - runs in thread pool"""
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'skip_download': True,  # Don't download, just extract info
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Get the direct video URL
                video_url = info.get('url')

                # If not directly available, get from formats
                if not video_url and info.get('formats'):
                    # Get best format with direct URL
                    for f in reversed(info['formats']):
                        if f.get('url') and f.get('ext') in ['mp4', 'webm', 'mov']:
                            video_url = f['url']
                            break

                if not video_url:
                    raise ValueError("Could not extract direct video URL")

                return {
                    "video_url": video_url,
                    "thumbnail_url": self._get_best_thumbnail(info),
                    "description": info.get("description", ""),
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                    "upload_date": info.get("upload_date"),
                    "uploader": info.get("uploader"),
                    "uploader_id": info.get("uploader_id"),
                    "channel": info.get("channel"),
                    "channel_url": info.get("channel_url"),
                    "platform": info.get("extractor", "").lower(),
                    "webpage_url": info.get("webpage_url"),
                }

        try:
            self.update_progress(10, ExtractionStep.VIDEO_DOWNLOADING)
            result = await asyncio.to_thread(_sync_extract_info)
            logger.info(
                f"Extracted video URL for client download: {result.get('title', 'Unknown')} "
                f"from {result.get('platform', 'unknown')}"
            )
            return result
        except Exception as e:
            logger.error(f"Error extracting video URL: {str(e)}")
            raise

    async def extract_from_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        extraction_job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract recipe content from a local video file.

        Used after the client uploads a video that was downloaded client-side.
        Processes the video file (audio extraction, transcription) and combines
        with previously extracted metadata.

        Args:
            file_path: Path to local video file
            metadata: Optional metadata from previous extract_video_url() call
            extraction_job_id: Optional job ID for cost tracking

        Returns:
            Dict containing transcript, description, and combined text
        """
        metadata = metadata or {}
        self._current_job_id = extraction_job_id

        try:
            # Track file for cleanup
            self._track_temp_file(file_path)

            self.update_progress(30, ExtractionStep.VIDEO_EXTRACTING_AUDIO)
            audio_path = await self._extract_audio(file_path)
            self._track_temp_file(audio_path)

            # Check feature flag for transcription method
            use_gemini = await self._should_use_gemini_transcription()
            if use_gemini:
                self.update_progress(50, ExtractionStep.GEMINI_TRANSCRIBING)
                transcript = await self._transcribe_audio_gemini(audio_path)
            else:
                self.update_progress(50, ExtractionStep.VIDEO_TRANSCRIBING)
                transcript = await self._transcribe_audio_whisper(audio_path)

            self.update_progress(90, ExtractionStep.VIDEO_COMBINING)

            # Get description from metadata or empty string
            description = metadata.get("description", "")

            # Combine transcript and description
            combined_text = f"""Video Description: {description}

Transcript:
{transcript}"""

            self.update_progress(100, ExtractionStep.COMPLETE)

            return {
                "text": combined_text.strip(),
                "transcript": transcript,
                "description": description,
                "video_path": file_path,
                # Include metadata from URL extraction
                "video_title": metadata.get("title"),
                "thumbnail_url": metadata.get("thumbnail_url"),
                "webpage_url": metadata.get("webpage_url"),
                "duration": metadata.get("duration"),
                "view_count": metadata.get("view_count"),
                "like_count": metadata.get("like_count"),
                "upload_date": metadata.get("upload_date"),
                "uploader": metadata.get("uploader"),
                "uploader_id": metadata.get("uploader_id"),
                "channel": metadata.get("channel"),
                "channel_url": metadata.get("channel_url"),
            }

        except Exception as e:
            logger.error(f"Error extracting from video file: {str(e)}")
            raise
        finally:
            # Always cleanup temp files, even on error
            self._cleanup_temp_files()
