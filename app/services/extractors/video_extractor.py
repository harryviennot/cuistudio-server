"""
Video extractor for TikTok, Reels, YouTube Shorts
"""
import os
import logging
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
            Dict containing transcript, ocr_text, description, and video_path
        """
        try:
            self.update_progress(10, "Downloading video")
            video_path, description = await self._download_video(source)

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
                "source_url": source
            }

        except Exception as e:
            logger.error(f"Error extracting from video: {str(e)}")
            raise

    async def _download_video(self, url: str) -> tuple[str, str]:
        """Download video using yt-dlp"""
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'{self.download_dir}/%(id)s.%(ext)s',
                'quiet': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                description = info.get('description', '')

                return video_path, description

        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise

    async def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video"""
        try:
            audio_path = video_path.replace(os.path.splitext(video_path)[1], '.mp3')

            video = VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path, logger=None)
            video.close()

            return audio_path

        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise

    async def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using OpenAI Whisper"""
        try:
            # Load Whisper model (using base model for speed)
            model = whisper.load_model("base")

            # Transcribe
            result = model.transcribe(audio_path)

            return result["text"]

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return ""

    async def _extract_key_frames(self, video_path: str, num_frames: int = 10) -> list[str]:
        """Extract key frames from video"""
        try:
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

        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            return []

    async def _run_ocr(self, frame_paths: list[str]) -> str:
        """Run OCR on frames using pytesseract"""
        try:
            import pytesseract
            from PIL import Image

            all_text = []

            for frame_path in frame_paths:
                image = Image.open(frame_path)
                text = pytesseract.image_to_string(image)
                if text.strip():
                    all_text.append(text.strip())

            return "\n\n".join(all_text)

        except Exception as e:
            logger.error(f"Error running OCR: {str(e)}")
            return ""
