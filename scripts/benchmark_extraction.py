#!/usr/bin/env python3
"""
Extraction Benchmark Script

Compares old (feature flags OFF) vs new (feature flags ON) extraction methods.
Measures:
- Speed (extraction time)
- Cost (AI API costs)
- Quality (side-by-side recipe JSON comparison)

Features:
- Simulates client-side download when server returns needs_client_download
- Downloads videos/images locally (simulating mobile client) and continues extraction
- Allows proper benchmarking of Instagram, Facebook, TikTok content

Usage:
    python scripts/benchmark_extraction.py --urls urls.txt
    python scripts/benchmark_extraction.py --url "https://tiktok.com/..."
    python scripts/benchmark_extraction.py --interactive

Requirements:
    - Set environment variables: SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY
    - Database migrations must be applied (feature_flags table)
"""

# Suppress warnings before imports
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import asyncio
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load .env from the cuisto-server directory (parent of scripts/)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Import after path setup
import yt_dlp
from supabase import create_client
from app.services.feature_flag_service import FeatureFlagService
from app.services.cost_tracker_service import CostTrackerService
from app.services.platform_status_service import PlatformStatusService
from app.services.gemini_service import GeminiService
from app.services.extractors.link_extractor import LinkExtractor
from app.services.extractors.video_extractor import VideoExtractor
from app.services.extractors.slideshow_extractor import SlideshowExtractor
from app.services.extractors.content_type_detector import ContentTypeDetector, ContentType


class BenchmarkMode(str, Enum):
    """Benchmark mode - which feature flags to enable"""
    LEGACY = "legacy"  # All flags OFF (current production behavior)
    NEW = "new"        # All flags ON (new Gemini stack)


@dataclass
class ExtractionResult:
    """Result of a single extraction attempt"""
    url: str
    mode: BenchmarkMode
    success: bool = False
    error: Optional[str] = None

    # Timing
    start_time: float = 0
    end_time: float = 0
    duration_seconds: float = 0

    # Content detection
    detected_type: Optional[str] = None
    platform: Optional[str] = None
    content_type_detected: Optional[str] = None

    # Cost tracking
    total_cost_usd: float = 0
    cost_breakdown: Dict[str, float] = field(default_factory=dict)

    # Recipe data
    recipe_data: Dict[str, Any] = field(default_factory=dict)

    # Raw extraction result
    raw_result: Dict[str, Any] = field(default_factory=dict)

    # Image URLs
    thumbnail_url: Optional[str] = None
    generated_image_url: Optional[str] = None

    # Raw extraction details
    raw_text: str = ""
    transcript: str = ""
    description: str = ""

    # Failure tracking
    failure_stage: Optional[str] = None  # "detection", "download", "extraction", "normalization"

    # Database job ID
    job_id: Optional[str] = None

    # Client download simulation
    client_download_simulated: bool = False


@dataclass
class BenchmarkComparison:
    """Comparison between legacy and new extraction for same URL"""
    url: str
    legacy_result: Optional[ExtractionResult] = None
    new_result: Optional[ExtractionResult] = None

    # Comparison metrics
    speed_diff_seconds: float = 0
    speed_diff_percent: float = 0
    cost_diff_usd: float = 0
    cost_diff_percent: float = 0

    # Quality comparison (field-by-field)
    quality_comparison: Dict[str, Any] = field(default_factory=dict)


class ExtractionBenchmark:
    """
    Benchmark tool for comparing extraction methods.

    Runs each URL through both legacy (flags OFF) and new (flags ON) modes,
    then compares speed, cost, and quality.
    """

    # Feature flags to toggle for new mode
    NEW_MODE_FLAGS = [
        "dynamic_content_detection",
        "slideshow_extraction",
        "vision_api_extraction",
        "dynamic_client_download",
        "gemini_3_text_extraction",
        "gemini_audio_transcription",
        "gemini_image_generation",
    ]

    # Benchmark user ID for database records (harry.viennot@icloud.com)
    BENCHMARK_USER_ID = "e6831fa3-48af-48e9-9139-cfc5d0ebb154"

    def __init__(
        self,
        skip_duplicates: bool = True,
        legacy_only: bool = False,
        new_only: bool = False,
        show_recipes: bool = False,
        simulate_client_download: bool = True
    ):
        """
        Initialize benchmark with Supabase client and services.

        Args:
            skip_duplicates: If True, bypasses duplicate detection (default True)
            legacy_only: Only run legacy mode
            new_only: Only run new mode
            show_recipes: Show full recipe JSON in output
            simulate_client_download: If True, simulate client-side download when needed (default True)
        """
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY/SUPABASE_SECRET_KEY must be set")

        self.supabase = create_client(supabase_url, supabase_key)
        self.feature_flags = FeatureFlagService(self.supabase)
        self.cost_tracker = CostTrackerService(self.supabase)
        self.platform_status = PlatformStatusService(self.supabase)

        # Benchmark options
        self.skip_duplicates = skip_duplicates
        self.legacy_only = legacy_only
        self.new_only = new_only
        self.show_recipes = show_recipes
        self.simulate_client_download = simulate_client_download

        # Results storage
        self.results: List[BenchmarkComparison] = []

        # Ensure benchmark user exists (for foreign key constraints)
        self._ensure_benchmark_user()

    def _ensure_benchmark_user(self) -> None:
        """
        Note: Benchmark jobs are created without user_id when the benchmark user
        doesn't exist in the users table. Cost tracking will still work via
        extraction_job_id if the job is created successfully.
        """
        # We don't create a fake user - instead, we'll create jobs without user_id
        # or skip job creation entirely if the schema requires it
        pass

    # ========================================
    # CLIENT-SIDE DOWNLOAD SIMULATION
    # ========================================

    async def _simulate_client_download_video(
        self,
        url: str,
        video_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Simulate client-side video download.

        In production, the mobile client downloads the video using their IP.
        For benchmarking locally, we can download directly since we have a
        different IP than the production VPS.

        Args:
            url: Original video URL (webpage URL)
            video_url: Direct video URL if available (from extract_video_url)

        Returns:
            Path to downloaded video file, or None if failed
        """
        download_dir = Path("temp/benchmark_videos")
        download_dir.mkdir(parents=True, exist_ok=True)

        def _sync_download():
            """Synchronous download - runs in thread pool"""
            ydl_opts = {
                'format': 'best',
                'outtmpl': str(download_dir / '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Use the original URL - yt-dlp will handle it
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                return video_path, info

        try:
            video_path, info = await asyncio.to_thread(_sync_download)
            print(f"    📥 Downloaded video: {Path(video_path).name}")
            return video_path
        except Exception as e:
            print(f"    ⚠️  Client download simulation failed: {e}")
            return None

    async def _simulate_client_download_images(
        self,
        url: str,
        thumbnail_url: Optional[str] = None
    ) -> List[bytes]:
        """
        Simulate client-side image download for slideshows.

        For TikTok photos and Instagram carousels, we try to extract
        image URLs using yt-dlp and download them.

        Args:
            url: Original slideshow URL
            thumbnail_url: Fallback thumbnail URL

        Returns:
            List of image bytes
        """
        import httpx

        images = []

        # Try to extract image URLs from yt-dlp
        def _sync_extract_images():
            """Extract image URLs from slideshow"""
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)

                    image_urls = []

                    # TikTok slideshows have images in 'entries' or 'thumbnails'
                    if info.get('entries'):
                        for entry in info['entries']:
                            if entry.get('url') and 'image' in entry.get('url', '').lower():
                                image_urls.append(entry['url'])
                            for thumb in entry.get('thumbnails', []):
                                if thumb.get('url'):
                                    image_urls.append(thumb['url'])

                    # Check thumbnails list
                    for thumb in info.get('thumbnails', []):
                        if thumb.get('url'):
                            image_urls.append(thumb['url'])

                    # Instagram may have image in 'url' directly
                    if info.get('url') and 'image' in info.get('url', '').lower():
                        image_urls.append(info['url'])

                    return list(dict.fromkeys(image_urls))  # Remove duplicates while preserving order

                except Exception as e:
                    print(f"    ⚠️  Could not extract image URLs: {e}")
                    return []

        try:
            image_urls = await asyncio.to_thread(_sync_extract_images)

            # Add thumbnail as fallback
            if thumbnail_url and thumbnail_url not in image_urls:
                image_urls.append(thumbnail_url)

            if not image_urls:
                print(f"    ⚠️  No image URLs found for slideshow")
                return []

            print(f"    📥 Downloading {len(image_urls)} images...")

            # Download images
            async with httpx.AsyncClient(timeout=15.0) as client:
                for img_url in image_urls[:5]:  # Limit to 5 images
                    try:
                        response = await client.get(
                            img_url,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'Accept': 'image/*,*/*;q=0.8',
                            },
                            follow_redirects=True
                        )
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', '')
                            if content_type.startswith('image/'):
                                images.append(response.content)
                    except Exception as e:
                        print(f"    ⚠️  Failed to download image: {e}")

            print(f"    ✓ Downloaded {len(images)} images")
            return images

        except Exception as e:
            print(f"    ⚠️  Image download simulation failed: {e}")
            return []

    async def _continue_extraction_with_video(
        self,
        video_path: str,
        metadata: Dict[str, Any],
        job_id: str,
        mode: BenchmarkMode
    ) -> Dict[str, Any]:
        """
        Continue extraction after simulated client download.

        Uses VideoExtractor.extract_from_file() to process the downloaded video.

        Args:
            video_path: Path to downloaded video file
            metadata: Metadata from initial extraction (description, thumbnail, etc.)
            job_id: Extraction job ID for cost tracking
            mode: Current benchmark mode

        Returns:
            Extraction result dict
        """
        gemini = GeminiService(feature_flag_service=self.feature_flags)

        video_extractor = VideoExtractor(
            feature_flag_service=self.feature_flags,
            gemini_service=gemini,
            cost_tracker=self.cost_tracker
        )

        result = await video_extractor.extract_from_file(
            file_path=video_path,
            metadata=metadata,
            extraction_job_id=job_id
        )

        result["detected_type"] = "video"
        result["client_download_simulated"] = True
        result["platform"] = metadata.get("platform")

        return result

    async def _continue_extraction_with_images(
        self,
        images: List[bytes],
        metadata: Dict[str, Any],
        source_url: str,
        job_id: str,
        mode: BenchmarkMode
    ) -> Dict[str, Any]:
        """
        Continue extraction after simulated client image download.

        Uses SlideshowExtractor to process the downloaded images with Vision API.

        Args:
            images: List of downloaded image bytes
            metadata: Metadata from initial extraction (description, thumbnail, etc.)
            source_url: Original URL
            job_id: Extraction job ID for cost tracking
            mode: Current benchmark mode

        Returns:
            Extraction result dict
        """
        gemini = GeminiService(feature_flag_service=self.feature_flags)

        # Use Gemini Vision API directly since we already have the image bytes
        result = await gemini.extract_recipe_from_images(
            images=images,
            context_description=metadata.get("description", ""),
            image_count=len(images)
        )

        # Track cost
        stats = result.get("_extraction_stats", {})
        await self.cost_tracker.record_cost(
            extraction_job_id=job_id,
            service_provider="gemini",
            service_type="vision",
            model_name=stats.get("model", "gemini-3-flash-preview"),
            input_tokens=stats.get("input_tokens"),
            output_tokens=stats.get("output_tokens"),
            images_processed=stats.get("image_count"),
            estimated_cost_usd=stats.get("estimated_cost_usd")
        )

        result["source_url"] = source_url
        result["detected_type"] = "slideshow"
        result["client_download_simulated"] = True
        result["platform"] = metadata.get("platform")
        result["image_count"] = len(images)
        result["description"] = metadata.get("description")

        if metadata.get("thumbnail_url"):
            result["image_url"] = metadata["thumbnail_url"]

        return result

    async def _create_extraction_job(self, url: str, mode: str) -> str:
        """
        Create a real extraction job in the database for cost tracking.

        Args:
            url: URL being extracted
            mode: "legacy" or "new"

        Returns:
            Job ID (UUID)
        """
        try:
            result = self.supabase.table("extraction_jobs").insert({
                "user_id": self.BENCHMARK_USER_ID,
                "source_type": "link",
                "source_url": url,
                "status": "processing",
                "progress_percentage": 0,
                "extraction_method": f"benchmark_{mode}"
            }).execute()
            return result.data[0]["id"]
        except Exception as e:
            print(f"  Warning: Failed to create extraction job: {e}")
            # Fall back to UUID if database insert fails
            import uuid
            return str(uuid.uuid4())

    async def _update_job_status(
        self,
        job_id: str,
        status: str,
        error: Optional[str] = None,
        content_type: Optional[str] = None,
        recipe_id: Optional[str] = None
    ) -> None:
        """
        Update extraction job status after completion/failure.

        Args:
            job_id: Job ID to update
            status: New status (completed, failed)
            error: Error message if failed
            content_type: Detected content type
            recipe_id: Created recipe ID if successful
        """
        try:
            update = {
                "status": status,
                "progress_percentage": 100 if status == "completed" else 0,
                "updated_at": datetime.utcnow().isoformat()
            }
            if error:
                update["error_message"] = error[:500]  # Truncate long errors
            if content_type:
                update["content_type"] = content_type
            if recipe_id:
                update["recipe_id"] = recipe_id

            self.supabase.table("extraction_jobs").update(update).eq("id", job_id).execute()
        except Exception as e:
            print(f"  Warning: Failed to update job status: {e}")

    async def set_feature_flags(self, mode: BenchmarkMode) -> None:
        """
        Set all feature flags for the given mode.

        Args:
            mode: LEGACY (all OFF) or NEW (all ON)
        """
        enabled = mode == BenchmarkMode.NEW

        for flag_name in self.NEW_MODE_FLAGS:
            try:
                # Update flag in database
                self.supabase.table("feature_flags").update({
                    "enabled": enabled,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("flag_name", flag_name).execute()
            except Exception as e:
                print(f"  Warning: Failed to set flag {flag_name}: {e}")

        # Invalidate cache to pick up changes
        self.feature_flags.invalidate_cache()

        print(f"  Feature flags set to: {'ON' if enabled else 'OFF'}")

    async def extract_url(
        self,
        url: str,
        mode: BenchmarkMode,
        job_id: str
    ) -> ExtractionResult:
        """
        Extract recipe from URL using specified mode.

        Args:
            url: URL to extract
            mode: Benchmark mode (LEGACY or NEW)
            job_id: Unique job ID for cost tracking

        Returns:
            ExtractionResult with timing, cost, and recipe data
        """
        result = ExtractionResult(url=url, mode=mode, job_id=job_id)

        # Create services for extraction
        gemini = GeminiService(feature_flag_service=self.feature_flags)

        extractor = LinkExtractor(
            feature_flag_service=self.feature_flags,
            platform_status_service=self.platform_status,
            gemini_service=gemini,
            cost_tracker=self.cost_tracker,
            skip_duplicate_check=self.skip_duplicates  # Bypass duplicates for benchmarking
        )

        # Start timing
        result.start_time = time.time()
        result.failure_stage = "detection"

        try:
            # Run extraction
            result.failure_stage = "extraction"
            extraction_result = await extractor.extract(
                source=url,
                extraction_job_id=job_id
            )

            result.end_time = time.time()
            result.duration_seconds = result.end_time - result.start_time
            result.raw_result = extraction_result

            # Extract metadata
            result.detected_type = extraction_result.get("detected_type")
            result.platform = extraction_result.get("platform")
            result.content_type_detected = extraction_result.get("content_type")

            # Extract image URLs
            result.thumbnail_url = extraction_result.get("thumbnail_url") or extraction_result.get("image_url")
            result.generated_image_url = extraction_result.get("generated_image_url")

            # Extract raw text data
            result.raw_text = extraction_result.get("text", "")
            result.transcript = extraction_result.get("transcript", "")
            result.description = extraction_result.get("description", "")

            # Check if this is a "needs_client_download" result
            # Simulate client-side download and continue extraction
            if extraction_result.get("needs_client_download"):
                if not self.simulate_client_download:
                    # Don't simulate - treat as failure
                    result.success = False
                    result.failure_stage = "client_download_required"
                    result.error = f"Requires client-side download ({result.platform or 'unknown platform'})"
                    await self._update_job_status(
                        job_id=job_id,
                        status="failed",
                        error=result.error,
                        content_type=result.content_type_detected
                    )
                    return result

                print(f"    🔄 Simulating client-side download...")

                content_type = extraction_result.get("content_type", "video")
                platform = extraction_result.get("platform")
                thumbnail_url = extraction_result.get("thumbnail_url")
                description = extraction_result.get("description", "")

                # Build metadata from initial result
                metadata = {
                    "platform": platform,
                    "description": description,
                    "thumbnail_url": thumbnail_url,
                    "title": extraction_result.get("title"),
                    "video_url": extraction_result.get("video_url"),
                    "webpage_url": extraction_result.get("webpage_url", url),
                }

                if content_type in ["slideshow", "image_post"]:
                    # Slideshow/image post - download images
                    images = await self._simulate_client_download_images(url, thumbnail_url)

                    if images:
                        # Continue extraction with downloaded images
                        extraction_result = await self._continue_extraction_with_images(
                            images=images,
                            metadata=metadata,
                            source_url=url,
                            job_id=job_id,
                            mode=mode
                        )
                        print(f"    ✓ Slideshow extraction completed with {len(images)} images")
                    else:
                        result.success = False
                        result.failure_stage = "client_download_failed"
                        result.error = f"Could not download images for slideshow ({platform})"
                        await self._update_job_status(
                            job_id=job_id,
                            status="failed",
                            error=result.error,
                            content_type=content_type
                        )
                        return result
                else:
                    # Video - download video file
                    video_path = await self._simulate_client_download_video(
                        url,
                        video_url=metadata.get("video_url")
                    )

                    if video_path:
                        # Continue extraction with downloaded video
                        extraction_result = await self._continue_extraction_with_video(
                            video_path=video_path,
                            metadata=metadata,
                            job_id=job_id,
                            mode=mode
                        )
                        print(f"    ✓ Video extraction completed")

                        # Clean up downloaded video
                        try:
                            Path(video_path).unlink()
                        except Exception:
                            pass
                    else:
                        result.success = False
                        result.failure_stage = "client_download_failed"
                        result.error = f"Could not download video ({platform})"
                        await self._update_job_status(
                            job_id=job_id,
                            status="failed",
                            error=result.error,
                            content_type=content_type
                        )
                        return result

                # Update result with new extraction data
                result.raw_result = extraction_result
                result.detected_type = extraction_result.get("detected_type")
                result.platform = extraction_result.get("platform")
                result.content_type_detected = extraction_result.get("content_type")
                result.thumbnail_url = extraction_result.get("thumbnail_url") or extraction_result.get("image_url")
                result.raw_text = extraction_result.get("text", "")
                result.transcript = extraction_result.get("transcript", "")
                result.description = extraction_result.get("description", "")
                result.client_download_simulated = True

            # Check if we actually got text content
            if not extraction_result.get("text"):
                result.success = False
                result.failure_stage = "no_text_extracted"
                result.error = "No text content extracted from source"
                await self._update_job_status(
                    job_id=job_id,
                    status="failed",
                    error=result.error,
                    content_type=result.content_type_detected
                )
                return result

            # Mark as success
            result.success = True
            result.failure_stage = None

            # Get costs from tracker
            costs = await self.cost_tracker.get_job_costs(job_id)
            result.total_cost_usd = sum(c.get("estimated_cost_usd", 0) or 0 for c in costs)

            # Build cost breakdown
            for cost in costs:
                provider = cost.get("service_provider", "unknown")
                service_type = cost.get("service_type", "unknown")
                key = f"{provider}/{service_type}"
                amount = cost.get("estimated_cost_usd", 0) or 0
                result.cost_breakdown[key] = result.cost_breakdown.get(key, 0) + amount

            # Normalize recipe if we have text
            try:
                result.failure_stage = "normalization"
                normalized = await gemini.normalize_recipe(
                    raw_content=extraction_result["text"],
                    source_type=result.detected_type or "link"
                )
                result.recipe_data = normalized
                result.failure_stage = None
            except Exception as e:
                print(f"    Warning: Normalization failed: {e}")
                result.recipe_data = {"error": str(e)}
                result.failure_stage = "normalization"

            # Update job status in database
            await self._update_job_status(
                job_id=job_id,
                status="completed",
                content_type=result.content_type_detected
            )

        except Exception as e:
            result.end_time = time.time()
            result.duration_seconds = result.end_time - result.start_time
            result.success = False
            result.error = str(e)

            # Update job status in database
            await self._update_job_status(
                job_id=job_id,
                status="failed",
                error=str(e)
            )

        return result

    def compare_recipes(
        self,
        legacy: Dict[str, Any],
        new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two recipe JSONs field by field.

        Args:
            legacy: Recipe from legacy extraction
            new: Recipe from new extraction

        Returns:
            Comparison dict with differences highlighted
        """
        comparison = {}

        # Fields to compare
        fields = [
            "title", "description", "servings", "prep_time", "cook_time",
            "total_time", "difficulty", "cuisine", "diet_tags",
            "ingredients", "instructions", "tips", "equipment"
        ]

        for field in fields:
            legacy_val = legacy.get(field)
            new_val = new.get(field)

            if legacy_val == new_val:
                comparison[field] = {
                    "status": "identical",
                    "value": legacy_val
                }
            else:
                comparison[field] = {
                    "status": "different",
                    "legacy": legacy_val,
                    "new": new_val,
                    "analysis": self._analyze_difference(field, legacy_val, new_val)
                }

        return comparison

    def _analyze_difference(
        self,
        field: str,
        legacy_val: Any,
        new_val: Any
    ) -> str:
        """Analyze the difference between two values."""
        if legacy_val is None and new_val is not None:
            return "NEW extracted value that LEGACY missed"
        elif legacy_val is not None and new_val is None:
            return "LEGACY had value that NEW missed"
        elif isinstance(legacy_val, list) and isinstance(new_val, list):
            legacy_count = len(legacy_val)
            new_count = len(new_val)
            if new_count > legacy_count:
                return f"NEW has more items ({new_count} vs {legacy_count})"
            elif legacy_count > new_count:
                return f"LEGACY has more items ({legacy_count} vs {new_count})"
            else:
                return "Same count, different content"
        elif isinstance(legacy_val, str) and isinstance(new_val, str):
            legacy_len = len(legacy_val)
            new_len = len(new_val)
            if abs(legacy_len - new_len) < 10:
                return "Minor text differences"
            elif new_len > legacy_len:
                return f"NEW is more detailed ({new_len} vs {legacy_len} chars)"
            else:
                return f"LEGACY is more detailed ({legacy_len} vs {new_len} chars)"
        else:
            return "Values differ"

    async def benchmark_url(self, url: str) -> BenchmarkComparison:
        """
        Run full benchmark on a single URL.

        Args:
            url: URL to benchmark

        Returns:
            BenchmarkComparison with both results and analysis
        """
        print(f"\n{'='*60}")
        print(f"Benchmarking: {url[:80]}...")
        print('='*60)

        comparison = BenchmarkComparison(url=url)

        step_count = 0
        if not self.new_only:
            step_count += 1
        if not self.legacy_only:
            step_count += 1

        current_step = 0

        # Run LEGACY mode (unless new_only)
        if not self.new_only:
            current_step += 1
            print(f"\n[{current_step}/{step_count}] Running LEGACY mode (flags OFF)...")
            await self.set_feature_flags(BenchmarkMode.LEGACY)
            await asyncio.sleep(0.5)  # Let cache invalidate

            # Create real extraction job in database
            legacy_job_id = await self._create_extraction_job(url, "legacy")

            comparison.legacy_result = await self.extract_url(
                url, BenchmarkMode.LEGACY, legacy_job_id
            )

            if comparison.legacy_result.success:
                client_dl = " (client download simulated)" if comparison.legacy_result.client_download_simulated else ""
                print(f"  ✓ Success in {comparison.legacy_result.duration_seconds:.2f}s{client_dl}")
                print(f"  Cost: ${comparison.legacy_result.total_cost_usd:.6f}")
                print(f"  Type: {comparison.legacy_result.detected_type}")
                if comparison.legacy_result.thumbnail_url:
                    print(f"  Thumbnail: {comparison.legacy_result.thumbnail_url[:60]}...")
                if self.show_recipes and comparison.legacy_result.recipe_data:
                    title = comparison.legacy_result.recipe_data.get("title", "Unknown")
                    print(f"  Recipe: {title}")
            else:
                print(f"  ✗ Failed at {comparison.legacy_result.failure_stage}: {comparison.legacy_result.error}")

        # Run NEW mode (unless legacy_only)
        if not self.legacy_only:
            current_step += 1
            print(f"\n[{current_step}/{step_count}] Running NEW mode (flags ON)...")
            await self.set_feature_flags(BenchmarkMode.NEW)
            await asyncio.sleep(0.5)  # Let cache invalidate

            # Create real extraction job in database
            new_job_id = await self._create_extraction_job(url, "new")

            comparison.new_result = await self.extract_url(
                url, BenchmarkMode.NEW, new_job_id
            )

            if comparison.new_result.success:
                client_dl = " (client download simulated)" if comparison.new_result.client_download_simulated else ""
                print(f"  ✓ Success in {comparison.new_result.duration_seconds:.2f}s{client_dl}")
                print(f"  Cost: ${comparison.new_result.total_cost_usd:.6f}")
                print(f"  Type: {comparison.new_result.detected_type}")
                if comparison.new_result.thumbnail_url:
                    print(f"  Thumbnail: {comparison.new_result.thumbnail_url[:60]}...")
                if comparison.new_result.generated_image_url:
                    print(f"  Generated: {comparison.new_result.generated_image_url[:60]}...")
                if self.show_recipes and comparison.new_result.recipe_data:
                    title = comparison.new_result.recipe_data.get("title", "Unknown")
                    ingredients = len(comparison.new_result.recipe_data.get("ingredients", []))
                    steps = len(comparison.new_result.recipe_data.get("instructions", []))
                    print(f"  Recipe: {title} ({ingredients} ingredients, {steps} steps)")
            else:
                print(f"  ✗ Failed at {comparison.new_result.failure_stage}: {comparison.new_result.error}")

        # Calculate comparison metrics (only if both modes ran)
        if comparison.legacy_result and comparison.new_result:
            legacy_time = comparison.legacy_result.duration_seconds
            new_time = comparison.new_result.duration_seconds

            comparison.speed_diff_seconds = new_time - legacy_time
            if legacy_time > 0:
                comparison.speed_diff_percent = ((new_time - legacy_time) / legacy_time) * 100

            legacy_cost = comparison.legacy_result.total_cost_usd
            new_cost = comparison.new_result.total_cost_usd

            comparison.cost_diff_usd = new_cost - legacy_cost
            if legacy_cost > 0:
                comparison.cost_diff_percent = ((new_cost - legacy_cost) / legacy_cost) * 100

            # Compare recipe quality
            if (comparison.legacy_result.recipe_data and
                comparison.new_result.recipe_data):
                comparison.quality_comparison = self.compare_recipes(
                    comparison.legacy_result.recipe_data,
                    comparison.new_result.recipe_data
                )

        # Reset flags to OFF after benchmark
        await self.set_feature_flags(BenchmarkMode.LEGACY)

        self.results.append(comparison)
        return comparison

    async def benchmark_urls(self, urls: List[str]) -> None:
        """
        Benchmark multiple URLs.

        Args:
            urls: List of URLs to benchmark
        """
        print(f"\nStarting benchmark of {len(urls)} URLs...")
        print("="*60)

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] ", end="")
            await self.benchmark_url(url)

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print benchmark summary."""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)

        successful = [r for r in self.results
                     if r.legacy_result and r.legacy_result.success
                     and r.new_result and r.new_result.success]

        if not successful:
            print("\nNo successful comparisons to summarize.")
            return

        # Speed comparison
        print("\n📊 SPEED COMPARISON")
        print("-"*40)
        total_legacy_time = sum(r.legacy_result.duration_seconds for r in successful)
        total_new_time = sum(r.new_result.duration_seconds for r in successful)

        print(f"  Total LEGACY time: {total_legacy_time:.2f}s")
        print(f"  Total NEW time:    {total_new_time:.2f}s")
        print(f"  Difference:        {total_new_time - total_legacy_time:+.2f}s")
        if total_legacy_time > 0:
            pct = ((total_new_time - total_legacy_time) / total_legacy_time) * 100
            print(f"  Change:            {pct:+.1f}%")

        # Cost comparison
        print("\n💰 COST COMPARISON")
        print("-"*40)
        total_legacy_cost = sum(r.legacy_result.total_cost_usd for r in successful)
        total_new_cost = sum(r.new_result.total_cost_usd for r in successful)

        print(f"  Total LEGACY cost: ${total_legacy_cost:.6f}")
        print(f"  Total NEW cost:    ${total_new_cost:.6f}")
        print(f"  Difference:        ${total_new_cost - total_legacy_cost:+.6f}")
        if total_legacy_cost > 0:
            pct = ((total_new_cost - total_legacy_cost) / total_legacy_cost) * 100
            print(f"  Change:            {pct:+.1f}%")

        # Quality summary
        print("\n✨ QUALITY SUMMARY")
        print("-"*40)

        identical_fields = 0
        different_fields = 0
        new_better = 0
        legacy_better = 0

        for result in successful:
            for field, comp in result.quality_comparison.items():
                if comp.get("status") == "identical":
                    identical_fields += 1
                else:
                    different_fields += 1
                    analysis = comp.get("analysis", "")
                    if "NEW" in analysis and "more" in analysis:
                        new_better += 1
                    elif "LEGACY" in analysis and "more" in analysis:
                        legacy_better += 1

        print(f"  Identical fields:  {identical_fields}")
        print(f"  Different fields:  {different_fields}")
        print(f"  NEW better:        {new_better}")
        print(f"  LEGACY better:     {legacy_better}")

        # Per-URL breakdown
        print("\n📋 PER-URL BREAKDOWN")
        print("-"*40)

        for result in self.results:
            url_short = result.url[:50] + "..." if len(result.url) > 50 else result.url
            print(f"\n  {url_short}")

            if result.legacy_result and result.new_result:
                if result.legacy_result.success and result.new_result.success:
                    print(f"    Speed: LEGACY {result.legacy_result.duration_seconds:.2f}s / "
                          f"NEW {result.new_result.duration_seconds:.2f}s "
                          f"({result.speed_diff_percent:+.1f}%)")
                    print(f"    Cost:  LEGACY ${result.legacy_result.total_cost_usd:.6f} / "
                          f"NEW ${result.new_result.total_cost_usd:.6f} "
                          f"({result.cost_diff_percent:+.1f}%)")
                    print(f"    Type:  {result.legacy_result.detected_type} → "
                          f"{result.new_result.detected_type}")
                else:
                    if not result.legacy_result.success:
                        print(f"    LEGACY failed: {result.legacy_result.error}")
                    if not result.new_result.success:
                        print(f"    NEW failed: {result.new_result.error}")

    def _serialize_result(self, result: ExtractionResult) -> Dict[str, Any]:
        """Serialize an ExtractionResult to a dict for JSON output."""
        return {
            "success": result.success,
            "error": result.error,
            "failure_stage": result.failure_stage,
            "duration_seconds": result.duration_seconds,
            "detected_type": result.detected_type,
            "content_type_detected": result.content_type_detected,
            "platform": result.platform,
            "total_cost_usd": result.total_cost_usd,
            "cost_breakdown": result.cost_breakdown,
            "recipe_data": result.recipe_data,
            "thumbnail_url": result.thumbnail_url,
            "generated_image_url": result.generated_image_url,
            "job_id": result.job_id,
            "client_download_simulated": result.client_download_simulated,
            # Include text data for debugging (truncated)
            "raw_text_preview": result.raw_text[:500] if result.raw_text else None,
            "transcript_preview": result.transcript[:500] if result.transcript else None,
            "description": result.description[:500] if result.description else None,
        }

    def save_results(self, output_path: str) -> None:
        """
        Save detailed results to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_urls": len(self.results),
            "benchmark_options": {
                "skip_duplicates": self.skip_duplicates,
                "legacy_only": self.legacy_only,
                "new_only": self.new_only,
                "simulate_client_download": self.simulate_client_download,
            },
            "results": []
        }

        for result in self.results:
            result_dict = {
                "url": result.url,
                "speed_diff_seconds": result.speed_diff_seconds,
                "speed_diff_percent": result.speed_diff_percent,
                "cost_diff_usd": result.cost_diff_usd,
                "cost_diff_percent": result.cost_diff_percent,
                "quality_comparison": result.quality_comparison,
            }

            if result.legacy_result:
                result_dict["legacy"] = self._serialize_result(result.legacy_result)

            if result.new_result:
                result_dict["new"] = self._serialize_result(result.new_result)

            output["results"].append(result_dict)

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        print(f"\n📁 Detailed results saved to: {output_path}")


async def detect_content_type(url: str) -> None:
    """Quick content type detection for a URL."""
    detector = ContentTypeDetector()
    result = await detector.detect(url)

    print(f"\nContent Type Detection for: {url}")
    print("-"*40)
    print(f"  Type:        {result.content_type.value}")
    print(f"  Platform:    {result.platform}")
    print(f"  Video ID:    {result.video_id}")
    print(f"  Has Audio:   {result.has_audio}")
    print(f"  Description: {result.description[:100] if result.description else 'None'}...")
    print(f"  Images:      {len(result.image_urls)} found")
    print(f"  Thumbnail:   {result.thumbnail_url}")


async def main():
    parser = argparse.ArgumentParser(
        description="Benchmark extraction methods (legacy vs new Gemini stack)"
    )

    parser.add_argument(
        "--url", "-u",
        type=str,
        help="Single URL to benchmark"
    )

    parser.add_argument(
        "--urls", "-f",
        type=str,
        help="File containing URLs (one per line)"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="benchmark_results.json",
        help="Output file for detailed results (default: benchmark_results.json)"
    )

    parser.add_argument(
        "--detect-only",
        action="store_true",
        help="Only run content type detection (no extraction)"
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode - enter URLs one by one"
    )

    # New benchmark options
    parser.add_argument(
        "--skip-duplicates",
        action="store_true",
        default=True,
        help="Skip duplicate detection (default: True, force re-extraction)"
    )

    parser.add_argument(
        "--no-skip-duplicates",
        action="store_true",
        help="Enable duplicate detection (use cached results if available)"
    )

    parser.add_argument(
        "--legacy-only",
        action="store_true",
        help="Only run legacy mode (flags OFF)"
    )

    parser.add_argument(
        "--new-only",
        action="store_true",
        help="Only run new mode (flags ON)"
    )

    parser.add_argument(
        "--show-recipes",
        action="store_true",
        help="Show full recipe details in output"
    )

    parser.add_argument(
        "--no-simulate-download",
        action="store_true",
        help="Don't simulate client-side download (treat needs_client_download as failure)"
    )

    args = parser.parse_args()

    # Collect URLs
    urls = []

    if args.url:
        urls.append(args.url)

    if args.urls:
        with open(args.urls, 'r') as f:
            urls.extend(line.strip() for line in f if line.strip() and not line.startswith('#'))

    if args.interactive:
        print("Interactive mode - enter URLs (empty line to finish):")
        while True:
            url = input("> ").strip()
            if not url:
                break
            urls.append(url)

    if not urls:
        parser.print_help()
        print("\nError: No URLs provided. Use --url, --urls, or --interactive")
        sys.exit(1)

    # Detect-only mode
    if args.detect_only:
        for url in urls:
            await detect_content_type(url)
        return

    # Determine skip_duplicates setting
    skip_duplicates = not args.no_skip_duplicates

    # Full benchmark
    benchmark = ExtractionBenchmark(
        skip_duplicates=skip_duplicates,
        legacy_only=args.legacy_only,
        new_only=args.new_only,
        show_recipes=args.show_recipes,
        simulate_client_download=not args.no_simulate_download
    )
    await benchmark.benchmark_urls(urls)
    benchmark.save_results(args.output)


if __name__ == "__main__":
    asyncio.run(main())
