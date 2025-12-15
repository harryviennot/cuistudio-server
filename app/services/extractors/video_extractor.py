"""
Video extractor for TikTok, Reels, YouTube Shorts

Simplified extraction flow:
1. Download video with yt-dlp (get metadata + thumbnail URL)
2. Extract audio with MoviePy
3. Transcribe audio with Whisper
4. Return transcript + description (no frame OCR)

NOTE: All blocking operations (yt-dlp, whisper, moviepy)
are wrapped in asyncio.to_thread() to prevent blocking the event loop.
This allows SSE progress events to be sent in real-time.
"""
import os
import logging
import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List

import yt_dlp
import whisper
from moviepy.video.io.VideoFileClip import VideoFileClip

from app.services.extractors.base_extractor import BaseExtractor
from app.core.config import get_settings

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

    def __init__(self, progress_callback=None):
        super().__init__(progress_callback)
        self.download_dir = "temp/videos"
        os.makedirs(self.download_dir, exist_ok=True)
        # Track temp files for cleanup
        self._temp_files: List[Path] = []

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

    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from video URL.

        Simplified flow (no frame OCR):
        1. Download video and get metadata
        2. Extract and transcribe audio
        3. Combine transcript with video description

        Args:
            source: Video URL (TikTok, Instagram, YouTube)

        Returns:
            Dict containing transcript, description, video metadata, and thumbnail URL
        """
        try:
            self.update_progress(5, "Downloading video")
            video_path, video_metadata = await self._download_video(source)
            self._track_temp_file(video_path)

            description = video_metadata.get("description", "")

            self.update_progress(30, "Extracting audio")
            audio_path = await self._extract_audio(video_path)
            self._track_temp_file(audio_path)

            self.update_progress(50, "Transcribing audio")
            transcript = await self._transcribe_audio(audio_path)

            self.update_progress(90, "Combining extracted content")

            # Combine transcript and description (no OCR text)
            combined_text = f"""Video Description: {description}

Transcript:
{transcript}"""

            self.update_progress(100, "Extraction complete")

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
                    "thumbnail": info.get("thumbnail"),

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

    async def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using OpenAI Whisper with cached model."""
        def _sync_transcribe():
            """Synchronous transcription - runs in thread pool (CPU-intensive)"""
            # Use cached Whisper model (loaded once per process)
            model = get_whisper_model(settings.WHISPER_MODEL)
            # Transcribe
            result = model.transcribe(audio_path)
            return result["text"]

        try:
            return await asyncio.to_thread(_sync_transcribe)
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return ""
