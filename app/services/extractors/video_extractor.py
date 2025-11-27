"""
Video extractor for TikTok, Reels, YouTube Shorts

NOTE: All blocking operations (yt-dlp, whisper, moviepy, cv2, pytesseract)
are wrapped in asyncio.to_thread() to prevent blocking the event loop.
This allows SSE progress events to be sent in real-time.
"""
import os
import logging
import asyncio
from typing import Dict, Any
import yt_dlp
import whisper
from moviepy.video.io.VideoFileClip import VideoFileClip
import cv2

from app.services.extractors.base_extractor import BaseExtractor
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VideoExtractor(BaseExtractor):
    """Extract recipes from video URLs (TikTok, Reels, Shorts)"""

    def __init__(self, progress_callback=None):
        super().__init__(progress_callback)
        self.download_dir = "temp/videos"
        os.makedirs(self.download_dir, exist_ok=True)

    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from video URL

        Args:
            source: Video URL (TikTok, Instagram, YouTube)

        Returns:
            Dict containing transcript, ocr_text, description, video metadata, and video_path
        """
        try:
            self.update_progress(10, "Downloading video")
            video_path, video_metadata = await self._download_video(source)

            description = video_metadata.get("description", "")

            self.update_progress(30, "Extracting audio")
            audio_path = await self._extract_audio(video_path)

            self.update_progress(50, "Transcribing audio")
            transcript = await self._transcribe_audio(audio_path)

            self.update_progress(70, "Extracting frames for OCR")
            frames = await self._extract_key_frames(video_path)

            self.update_progress(85, "Running OCR on frames")
            ocr_text = await self._run_ocr(frames)

            self.update_progress(95, "Combining extracted content")

            # Combine all extracted text
            combined_text = f"""
Video Description: {description}

Transcript:
{transcript}

Text from Video (OCR):
{ocr_text}
"""

            self.update_progress(100, "Extraction complete")

            return {
                "text": combined_text.strip(),
                "transcript": transcript,
                "ocr_text": ocr_text,
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
        """Extract audio from video"""
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
        """Transcribe audio using OpenAI Whisper"""
        def _sync_transcribe():
            """Synchronous transcription - runs in thread pool (CPU-intensive)"""
            # Load Whisper model (using base model for speed)
            model = whisper.load_model("base")
            # Transcribe
            result = model.transcribe(audio_path)
            return result["text"]

        try:
            return await asyncio.to_thread(_sync_transcribe)
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return ""

    async def _extract_key_frames(self, video_path: str, num_frames: int = 10) -> list[str]:
        """Extract key frames from video"""
        def _sync_extract_frames():
            """Synchronous frame extraction - runs in thread pool"""
            frames_dir = "temp/frames"
            os.makedirs(frames_dir, exist_ok=True)

            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            frame_interval = max(1, total_frames // num_frames)
            frame_paths = []

            for i in range(0, total_frames, frame_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()

                if ret:
                    frame_path = f"{frames_dir}/frame_{i}.jpg"
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)

                if len(frame_paths) >= num_frames:
                    break

            cap.release()
            return frame_paths

        try:
            return await asyncio.to_thread(_sync_extract_frames)
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            return []

    async def _run_ocr(self, frame_paths: list[str]) -> str:
        """Run OCR on frames using pytesseract"""
        def _sync_ocr():
            """Synchronous OCR - runs in thread pool"""
            import pytesseract
            from PIL import Image

            all_text = []

            for frame_path in frame_paths:
                image = Image.open(frame_path)
                text = pytesseract.image_to_string(image)
                if text.strip():
                    all_text.append(text.strip())

            return "\n\n".join(all_text)

        try:
            return await asyncio.to_thread(_sync_ocr)
        except Exception as e:
            logger.error(f"Error running OCR: {str(e)}")
            return ""
