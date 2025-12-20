#!/usr/bin/env python3
"""
Comprehensive benchmark script for comparing recipe extraction strategies.
Runs extraction directly without needing the server.

Compares multiple strategies for both video and photo extraction:

VIDEO STRATEGIES:
- full: Complete extraction (description + transcript + OCR + normalize + image gen)
- no_ocr: Skip frame OCR (description + transcript + normalize + image gen)
- description_only: Only video metadata (title + description + normalize)
- transcript_only: Only audio transcript (download + transcribe + normalize)
- no_image_gen: Full extraction without Flux image generation

PHOTO STRATEGIES:
- full: OCR + GPT-4o-mini with image (current production)
- ocr_only: OCR + GPT-4o-mini with only OCR text
- vision_only: GPT-4o-mini with image only, no OCR

Usage:
    cd cuistudio-server
    source venv/bin/activate

    # Run with config file
    python scripts/benchmark_extraction_full.py --config benchmark_inputs/config.json

    # Test specific video(s)
    python scripts/benchmark_extraction_full.py --video "https://tiktok.com/..." --strategies full,no_ocr

    # Test specific photo(s)
    python scripts/benchmark_extraction_full.py --photo "path/to/image.jpg" --strategies full,ocr_only,vision_only

    # Specify output format
    python scripts/benchmark_extraction_full.py --config config.json --format markdown,json,csv
"""

import asyncio
import sys
import os
import time
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod

# Add the app to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.openai_service import OpenAIService
from app.services.extractors.photo_extractor import PhotoExtractor
from app.services.extractors.video_extractor import VideoExtractor
from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

settings = get_settings()

# Default paths
PROJECT_ROOT = Path(__file__).parent.parent.parent  # recipe-app/
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "benchmark_results"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class StepTiming:
    """Timing for a single extraction step"""
    step_name: str
    duration_seconds: float


@dataclass
class CostBreakdown:
    """Cost breakdown for an extraction"""
    openai_prompt_tokens: int = 0
    openai_completion_tokens: int = 0
    openai_total_tokens: int = 0
    openai_cost_usd: float = 0.0
    flux_image_cost_usd: float = 0.0

    @property
    def total_cost_usd(self) -> float:
        return self.openai_cost_usd + self.flux_image_cost_usd


@dataclass
class QualityIndicators:
    """Quality indicators for recipe extraction"""
    has_title: bool = False
    has_description: bool = False
    ingredient_count: int = 0
    instruction_count: int = 0
    has_servings: bool = False
    has_difficulty: bool = False
    has_prep_time: bool = False
    has_cook_time: bool = False
    has_total_time: bool = False
    tag_count: int = 0
    category_count: int = 0


@dataclass
class BenchmarkResult:
    """Result of a single extraction benchmark"""
    strategy: str
    success: bool
    error_message: Optional[str] = None
    total_time_seconds: float = 0.0
    step_timings: List[StepTiming] = field(default_factory=list)
    cost: Optional[CostBreakdown] = None
    quality: Optional[QualityIndicators] = None
    recipe_data: Optional[Dict[str, Any]] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_quality_indicators(recipe_data: Dict[str, Any]) -> QualityIndicators:
    """Extract quality indicators from recipe data"""
    return QualityIndicators(
        has_title=bool(recipe_data.get("title")),
        has_description=bool(recipe_data.get("description")),
        ingredient_count=len(recipe_data.get("ingredients", [])),
        instruction_count=len(recipe_data.get("instructions", [])),
        has_servings=recipe_data.get("servings") is not None,
        has_difficulty=bool(recipe_data.get("difficulty")),
        has_prep_time=recipe_data.get("prep_time_minutes") is not None,
        has_cook_time=recipe_data.get("cook_time_minutes") is not None,
        has_total_time=recipe_data.get("total_time_minutes") is not None,
        tag_count=len(recipe_data.get("tags", [])),
        category_count=len(recipe_data.get("categories", []))
    )


def extract_cost_from_stats(stats: Dict[str, Any], include_image: bool = False) -> CostBreakdown:
    """Extract cost breakdown from extraction stats"""
    return CostBreakdown(
        openai_prompt_tokens=stats.get("prompt_tokens", 0),
        openai_completion_tokens=stats.get("completion_tokens", 0),
        openai_total_tokens=stats.get("total_tokens", 0),
        openai_cost_usd=stats.get("estimated_cost_usd", 0.0),
        flux_image_cost_usd=0.04 if include_image else 0.0
    )


# =============================================================================
# VIDEO STRATEGIES
# =============================================================================

class VideoStrategy(ABC):
    """Base class for video extraction strategies"""

    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.extractor = VideoExtractor()

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def run(self, url: str) -> BenchmarkResult:
        pass


class VideoFullStrategy(VideoStrategy):
    """Full video extraction: description + transcript + OCR + normalize (no image gen in benchmark)"""

    name = "full"
    description = "Complete extraction with all steps (description + transcript + OCR + normalize)"

    async def run(self, url: str) -> BenchmarkResult:
        total_start = time.time()
        step_timings = []

        try:
            # Step 1: Download video
            step_start = time.time()
            video_path, metadata = await self.extractor._download_video(url)
            self.extractor._track_temp_file(video_path)
            step_timings.append(StepTiming("download", time.time() - step_start))

            description = metadata.get("description", "")
            video_title = metadata.get("title", "")

            # Step 2: Extract audio + frames (parallel)
            step_start = time.time()
            audio_task = asyncio.create_task(self.extractor._extract_audio(video_path))
            frames_task = asyncio.create_task(self.extractor._extract_key_frames(video_path))
            audio_path, frames = await asyncio.gather(audio_task, frames_task)
            self.extractor._track_temp_file(audio_path)
            for frame in frames:
                self.extractor._track_temp_file(frame)
            step_timings.append(StepTiming("audio_frames_extraction", time.time() - step_start))

            # Step 3: Transcribe + OCR (parallel)
            step_start = time.time()
            transcript_task = asyncio.create_task(self.extractor._transcribe_audio(audio_path))
            ocr_task = asyncio.create_task(self.extractor._run_ocr(frames))
            transcript, ocr_text = await asyncio.gather(transcript_task, ocr_task)
            step_timings.append(StepTiming("transcribe_ocr", time.time() - step_start))

            # Step 4: Combine and normalize
            step_start = time.time()
            combined_text = f"""
Video Title: {video_title}

Video Description: {description}

Transcript:
{transcript}

Text from Video (OCR):
{ocr_text}
"""
            normalized = await self.openai_service.normalize_recipe(combined_text.strip(), "video")
            step_timings.append(StepTiming("normalize", time.time() - step_start))

            # Extract metrics
            stats = normalized.pop("_extraction_stats", {}) if "_extraction_stats" in normalized else {}
            cost = extract_cost_from_stats(stats, include_image=False)
            quality = extract_quality_indicators(normalized)

            return BenchmarkResult(
                strategy=self.name,
                success=True,
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings,
                cost=cost,
                quality=quality,
                recipe_data=normalized
            )

        except Exception as e:
            return BenchmarkResult(
                strategy=self.name,
                success=False,
                error_message=str(e),
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings
            )
        finally:
            self.extractor._cleanup_temp_files()


class VideoNoOcrStrategy(VideoStrategy):
    """Video extraction without OCR: description + transcript only"""

    name = "no_ocr"
    description = "Skip frame OCR (description + transcript + normalize)"

    async def run(self, url: str) -> BenchmarkResult:
        total_start = time.time()
        step_timings = []

        try:
            # Step 1: Download video
            step_start = time.time()
            video_path, metadata = await self.extractor._download_video(url)
            self.extractor._track_temp_file(video_path)
            step_timings.append(StepTiming("download", time.time() - step_start))

            description = metadata.get("description", "")
            video_title = metadata.get("title", "")

            # Step 2: Extract audio only
            step_start = time.time()
            audio_path = await self.extractor._extract_audio(video_path)
            self.extractor._track_temp_file(audio_path)
            step_timings.append(StepTiming("audio_extraction", time.time() - step_start))

            # Step 3: Transcribe only (no OCR)
            step_start = time.time()
            transcript = await self.extractor._transcribe_audio(audio_path)
            step_timings.append(StepTiming("transcribe", time.time() - step_start))

            # Step 4: Normalize (without OCR text)
            step_start = time.time()
            combined_text = f"""
Video Title: {video_title}

Video Description: {description}

Transcript:
{transcript}
"""
            normalized = await self.openai_service.normalize_recipe(combined_text.strip(), "video")
            step_timings.append(StepTiming("normalize", time.time() - step_start))

            # Extract metrics
            stats = normalized.pop("_extraction_stats", {}) if "_extraction_stats" in normalized else {}
            cost = extract_cost_from_stats(stats, include_image=False)
            quality = extract_quality_indicators(normalized)

            return BenchmarkResult(
                strategy=self.name,
                success=True,
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings,
                cost=cost,
                quality=quality,
                recipe_data=normalized
            )

        except Exception as e:
            return BenchmarkResult(
                strategy=self.name,
                success=False,
                error_message=str(e),
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings
            )
        finally:
            self.extractor._cleanup_temp_files()


class VideoDescriptionOnlyStrategy(VideoStrategy):
    """Video extraction using only title and description from metadata"""

    name = "description_only"
    description = "Only video metadata (title + description + normalize)"

    async def run(self, url: str) -> BenchmarkResult:
        total_start = time.time()
        step_timings = []

        try:
            # Step 1: Download video (just for metadata)
            step_start = time.time()
            video_path, metadata = await self.extractor._download_video(url)
            self.extractor._track_temp_file(video_path)
            step_timings.append(StepTiming("download", time.time() - step_start))

            description = metadata.get("description", "")
            video_title = metadata.get("title", "")

            # Step 2: Normalize from metadata only
            step_start = time.time()
            combined_text = f"""
Video Title: {video_title}

Video Description: {description}
"""
            normalized = await self.openai_service.normalize_recipe(combined_text.strip(), "video")
            step_timings.append(StepTiming("normalize", time.time() - step_start))

            # Extract metrics
            stats = normalized.pop("_extraction_stats", {}) if "_extraction_stats" in normalized else {}
            cost = extract_cost_from_stats(stats, include_image=False)
            quality = extract_quality_indicators(normalized)

            return BenchmarkResult(
                strategy=self.name,
                success=True,
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings,
                cost=cost,
                quality=quality,
                recipe_data=normalized
            )

        except Exception as e:
            return BenchmarkResult(
                strategy=self.name,
                success=False,
                error_message=str(e),
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings
            )
        finally:
            self.extractor._cleanup_temp_files()


class VideoTranscriptOnlyStrategy(VideoStrategy):
    """Video extraction using only audio transcript"""

    name = "transcript_only"
    description = "Only audio transcript (download + transcribe + normalize)"

    async def run(self, url: str) -> BenchmarkResult:
        total_start = time.time()
        step_timings = []

        try:
            # Step 1: Download video
            step_start = time.time()
            video_path, metadata = await self.extractor._download_video(url)
            self.extractor._track_temp_file(video_path)
            step_timings.append(StepTiming("download", time.time() - step_start))

            # Step 2: Extract audio
            step_start = time.time()
            audio_path = await self.extractor._extract_audio(video_path)
            self.extractor._track_temp_file(audio_path)
            step_timings.append(StepTiming("audio_extraction", time.time() - step_start))

            # Step 3: Transcribe
            step_start = time.time()
            transcript = await self.extractor._transcribe_audio(audio_path)
            step_timings.append(StepTiming("transcribe", time.time() - step_start))

            # Step 4: Normalize from transcript only
            step_start = time.time()
            combined_text = f"""
Transcript:
{transcript}
"""
            normalized = await self.openai_service.normalize_recipe(combined_text.strip(), "video")
            step_timings.append(StepTiming("normalize", time.time() - step_start))

            # Extract metrics
            stats = normalized.pop("_extraction_stats", {}) if "_extraction_stats" in normalized else {}
            cost = extract_cost_from_stats(stats, include_image=False)
            quality = extract_quality_indicators(normalized)

            return BenchmarkResult(
                strategy=self.name,
                success=True,
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings,
                cost=cost,
                quality=quality,
                recipe_data=normalized
            )

        except Exception as e:
            return BenchmarkResult(
                strategy=self.name,
                success=False,
                error_message=str(e),
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings
            )
        finally:
            self.extractor._cleanup_temp_files()


# =============================================================================
# PHOTO STRATEGIES
# =============================================================================

class PhotoStrategy(ABC):
    """Base class for photo extraction strategies"""

    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.extractor = PhotoExtractor()

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def run(self, image_path: str) -> BenchmarkResult:
        pass


class PhotoFullStrategy(PhotoStrategy):
    """Full photo extraction: OCR + GPT-4o-mini with image"""

    name = "full"
    description = "OCR + GPT-4o-mini Vision (image + OCR text)"

    async def run(self, image_path: str) -> BenchmarkResult:
        total_start = time.time()
        step_timings = []

        try:
            # Step 0: Convert HEIC to JPEG if needed
            step_start = time.time()
            converted_path = await self.extractor._convert_image_if_needed(image_path)
            if converted_path != image_path:
                step_timings.append(StepTiming("heic_conversion", time.time() - step_start))

            # Step 1: Run OCR
            step_start = time.time()
            ocr_text = await self.extractor._run_ocr(image_path)
            step_timings.append(StepTiming("ocr", time.time() - step_start))

            # Step 2: Extract with vision (use converted path for OpenAI)
            step_start = time.time()
            recipe_data = await self.openai_service.extract_recipe_from_image_with_ocr(
                converted_path, ocr_text
            )
            step_timings.append(StepTiming("vision_extraction", time.time() - step_start))

            # Extract metrics
            stats = recipe_data.pop("_extraction_stats", {}) if "_extraction_stats" in recipe_data else {}
            cost = extract_cost_from_stats(stats, include_image=False)
            quality = extract_quality_indicators(recipe_data)

            return BenchmarkResult(
                strategy=self.name,
                success=True,
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings,
                cost=cost,
                quality=quality,
                recipe_data=recipe_data
            )

        except Exception as e:
            return BenchmarkResult(
                strategy=self.name,
                success=False,
                error_message=str(e),
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings
            )


class PhotoOcrOnlyStrategy(PhotoStrategy):
    """OCR text only, no image sent to GPT"""

    name = "ocr_only"
    description = "OCR + GPT-4o-mini (OCR text only, no image)"

    async def run(self, image_path: str) -> BenchmarkResult:
        total_start = time.time()
        step_timings = []

        try:
            # Step 1: Run OCR
            step_start = time.time()
            ocr_text = await self.extractor._run_ocr(image_path)
            step_timings.append(StepTiming("ocr", time.time() - step_start))

            # Step 2: Extract from OCR only
            step_start = time.time()
            recipe_data = await self.openai_service.extract_recipe_from_ocr_text_only(ocr_text)
            step_timings.append(StepTiming("text_extraction", time.time() - step_start))

            # Extract metrics
            stats = recipe_data.pop("_extraction_stats", {}) if "_extraction_stats" in recipe_data else {}
            cost = extract_cost_from_stats(stats, include_image=False)
            quality = extract_quality_indicators(recipe_data)

            return BenchmarkResult(
                strategy=self.name,
                success=True,
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings,
                cost=cost,
                quality=quality,
                recipe_data=recipe_data
            )

        except Exception as e:
            return BenchmarkResult(
                strategy=self.name,
                success=False,
                error_message=str(e),
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings
            )


class PhotoVisionOnlyStrategy(PhotoStrategy):
    """Image to GPT without OCR preprocessing"""

    name = "vision_only"
    description = "GPT-4o-mini Vision (image only, skip OCR)"

    async def run(self, image_path: str) -> BenchmarkResult:
        total_start = time.time()
        step_timings = []

        try:
            # Step 0: Convert HEIC to JPEG if needed
            step_start = time.time()
            converted_path = await self.extractor._convert_image_if_needed(image_path)
            if converted_path != image_path:
                step_timings.append(StepTiming("heic_conversion", time.time() - step_start))

            # Step 1: Extract with vision only (no OCR)
            step_start = time.time()
            recipe_data = await self.openai_service.extract_recipe_from_image_only(converted_path)
            step_timings.append(StepTiming("vision_extraction", time.time() - step_start))

            # Extract metrics
            stats = recipe_data.pop("_extraction_stats", {}) if "_extraction_stats" in recipe_data else {}
            cost = extract_cost_from_stats(stats, include_image=False)
            quality = extract_quality_indicators(recipe_data)

            return BenchmarkResult(
                strategy=self.name,
                success=True,
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings,
                cost=cost,
                quality=quality,
                recipe_data=recipe_data
            )

        except Exception as e:
            return BenchmarkResult(
                strategy=self.name,
                success=False,
                error_message=str(e),
                total_time_seconds=time.time() - total_start,
                step_timings=step_timings
            )


# =============================================================================
# STRATEGY FACTORIES
# =============================================================================

VIDEO_STRATEGIES = {
    "full": VideoFullStrategy,
    "no_ocr": VideoNoOcrStrategy,
    "description_only": VideoDescriptionOnlyStrategy,
    "transcript_only": VideoTranscriptOnlyStrategy,
}

PHOTO_STRATEGIES = {
    "full": PhotoFullStrategy,
    "ocr_only": PhotoOcrOnlyStrategy,
    "vision_only": PhotoVisionOnlyStrategy,
}


def create_video_strategies(strategy_names: List[str], openai_service: OpenAIService) -> List[VideoStrategy]:
    """Create video strategy instances"""
    strategies = []
    for name in strategy_names:
        if name in VIDEO_STRATEGIES:
            strategies.append(VIDEO_STRATEGIES[name](openai_service))
        else:
            logger.warning(f"Unknown video strategy: {name}")
    return strategies


def create_photo_strategies(strategy_names: List[str], openai_service: OpenAIService) -> List[PhotoStrategy]:
    """Create photo strategy instances"""
    strategies = []
    for name in strategy_names:
        if name in PHOTO_STRATEGIES:
            strategies.append(PHOTO_STRATEGIES[name](openai_service))
        else:
            logger.warning(f"Unknown photo strategy: {name}")
    return strategies


# =============================================================================
# BENCHMARK RUNNERS
# =============================================================================

async def run_video_benchmarks(
    urls: List[str],
    strategy_names: List[str],
    openai_service: OpenAIService
) -> Dict[str, Dict[str, BenchmarkResult]]:
    """Run video benchmarks for all URLs and strategies"""
    results = {}
    strategies = create_video_strategies(strategy_names, openai_service)

    for url in urls:
        url_key = url[:60] + "..." if len(url) > 60 else url
        print(f"\n{'='*60}")
        print(f"VIDEO: {url_key}")
        print(f"{'='*60}")

        results[url] = {}

        for strategy in strategies:
            print(f"\n  Strategy: {strategy.name} ({strategy.description})")
            result = await strategy.run(url)
            results[url][strategy.name] = result

            if result.success:
                print(f"    SUCCESS: {result.total_time_seconds:.2f}s")
                if result.cost:
                    print(f"    Tokens: {result.cost.openai_total_tokens}, Cost: ${result.cost.total_cost_usd:.4f}")
                if result.quality:
                    print(f"    Quality: {result.quality.ingredient_count} ingredients, {result.quality.instruction_count} steps")
                # Print step breakdown
                print("    Steps:")
                for step in result.step_timings:
                    print(f"      - {step.step_name}: {step.duration_seconds:.2f}s")
            else:
                print(f"    FAILED: {result.error_message}")

    return results


async def run_photo_benchmarks(
    paths: List[str],
    strategy_names: List[str],
    openai_service: OpenAIService
) -> Dict[str, Dict[str, BenchmarkResult]]:
    """Run photo benchmarks for all paths and strategies"""
    results = {}
    strategies = create_photo_strategies(strategy_names, openai_service)

    for path in paths:
        path_name = Path(path).name
        print(f"\n{'='*60}")
        print(f"PHOTO: {path_name}")
        print(f"{'='*60}")

        if not os.path.exists(path):
            print("  SKIP: File not found")
            continue

        results[path] = {}

        for strategy in strategies:
            print(f"\n  Strategy: {strategy.name} ({strategy.description})")
            result = await strategy.run(path)
            results[path][strategy.name] = result

            if result.success:
                print(f"    SUCCESS: {result.total_time_seconds:.2f}s")
                if result.cost:
                    print(f"    Tokens: {result.cost.openai_total_tokens}, Cost: ${result.cost.total_cost_usd:.4f}")
                if result.quality:
                    print(f"    Quality: {result.quality.ingredient_count} ingredients, {result.quality.instruction_count} steps")
                # Print step breakdown
                print("    Steps:")
                for step in result.step_timings:
                    print(f"      - {step.step_name}: {step.duration_seconds:.2f}s")
            else:
                print(f"    FAILED: {result.error_message}")

    return results


# =============================================================================
# REPORT GENERATORS
# =============================================================================

def result_to_dict(result: BenchmarkResult) -> Dict[str, Any]:
    """Convert BenchmarkResult to serializable dict"""
    data = {
        "strategy": result.strategy,
        "success": result.success,
        "error_message": result.error_message,
        "total_time_seconds": result.total_time_seconds,
        "step_timings": [{"step_name": s.step_name, "duration_seconds": s.duration_seconds} for s in result.step_timings],
    }
    if result.cost:
        data["cost"] = {
            "openai_prompt_tokens": result.cost.openai_prompt_tokens,
            "openai_completion_tokens": result.cost.openai_completion_tokens,
            "openai_total_tokens": result.cost.openai_total_tokens,
            "openai_cost_usd": result.cost.openai_cost_usd,
            "flux_image_cost_usd": result.cost.flux_image_cost_usd,
            "total_cost_usd": result.cost.total_cost_usd,
        }
    if result.quality:
        data["quality"] = asdict(result.quality)
    if result.recipe_data:
        data["recipe_data"] = result.recipe_data
    return data


def generate_json_report(
    video_results: Dict[str, Dict[str, BenchmarkResult]],
    photo_results: Dict[str, Dict[str, BenchmarkResult]]
) -> Dict[str, Any]:
    """Generate JSON report"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "video_benchmarks": {},
        "photo_benchmarks": {},
    }

    for url, strategies in video_results.items():
        report["video_benchmarks"][url] = {
            name: result_to_dict(result) for name, result in strategies.items()
        }

    for path, strategies in photo_results.items():
        report["photo_benchmarks"][path] = {
            name: result_to_dict(result) for name, result in strategies.items()
        }

    return report


def generate_markdown_report(
    video_results: Dict[str, Dict[str, BenchmarkResult]],
    photo_results: Dict[str, Dict[str, BenchmarkResult]]
) -> str:
    """Generate Markdown report"""
    lines = []
    lines.append("# Recipe Extraction Benchmark Report")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Video benchmarks
    if video_results:
        lines.append("## Video Benchmarks")
        lines.append("")

        for url, strategies in video_results.items():
            url_display = url[:60] + "..." if len(url) > 60 else url
            lines.append(f"### Video: {url_display}")
            lines.append("")
            lines.append("| Strategy | Time | Tokens | Cost | Ingredients | Steps | Status |")
            lines.append("|----------|------|--------|------|-------------|-------|--------|")

            for name, result in strategies.items():
                if result.success:
                    tokens = result.cost.openai_total_tokens if result.cost else "N/A"
                    cost = f"${result.cost.total_cost_usd:.4f}" if result.cost else "N/A"
                    ingredients = result.quality.ingredient_count if result.quality else "N/A"
                    steps = result.quality.instruction_count if result.quality else "N/A"
                    status = "OK"
                else:
                    tokens = "N/A"
                    cost = "N/A"
                    ingredients = "N/A"
                    steps = "N/A"
                    status = "FAILED"

                lines.append(f"| {name} | {result.total_time_seconds:.2f}s | {tokens} | {cost} | {ingredients} | {steps} | {status} |")

            lines.append("")

            # Step timing breakdown for full strategy
            if "full" in strategies and strategies["full"].success:
                lines.append("**Step Timing Breakdown (full strategy):**")
                for step in strategies["full"].step_timings:
                    lines.append(f"- {step.step_name}: {step.duration_seconds:.2f}s")
                lines.append("")

    # Photo benchmarks
    if photo_results:
        lines.append("## Photo Benchmarks")
        lines.append("")

        for path, strategies in photo_results.items():
            path_display = Path(path).name
            lines.append(f"### Photo: {path_display}")
            lines.append("")
            lines.append("| Strategy | Time | Tokens | Cost | Ingredients | Steps | Status |")
            lines.append("|----------|------|--------|------|-------------|-------|--------|")

            for name, result in strategies.items():
                if result.success:
                    tokens = result.cost.openai_total_tokens if result.cost else "N/A"
                    cost = f"${result.cost.total_cost_usd:.4f}" if result.cost else "N/A"
                    ingredients = result.quality.ingredient_count if result.quality else "N/A"
                    steps = result.quality.instruction_count if result.quality else "N/A"
                    status = "OK"
                else:
                    tokens = "N/A"
                    cost = "N/A"
                    ingredients = "N/A"
                    steps = "N/A"
                    status = "FAILED"

                lines.append(f"| {name} | {result.total_time_seconds:.2f}s | {tokens} | {cost} | {ingredients} | {steps} | {status} |")

            lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")

    # Calculate averages
    all_results = []
    for strategies in list(video_results.values()) + list(photo_results.values()):
        for result in strategies.values():
            if result.success:
                all_results.append(result)

    if all_results:
        # Group by strategy
        strategy_stats = {}
        for result in all_results:
            if result.strategy not in strategy_stats:
                strategy_stats[result.strategy] = {"times": [], "costs": [], "ingredients": [], "steps": []}
            strategy_stats[result.strategy]["times"].append(result.total_time_seconds)
            if result.cost:
                strategy_stats[result.strategy]["costs"].append(result.cost.total_cost_usd)
            if result.quality:
                strategy_stats[result.strategy]["ingredients"].append(result.quality.ingredient_count)
                strategy_stats[result.strategy]["steps"].append(result.quality.instruction_count)

        lines.append("| Strategy | Avg Time | Avg Cost | Avg Ingredients | Avg Steps |")
        lines.append("|----------|----------|----------|-----------------|-----------|")

        for name, stats in strategy_stats.items():
            avg_time = sum(stats["times"]) / len(stats["times"]) if stats["times"] else 0
            avg_cost = sum(stats["costs"]) / len(stats["costs"]) if stats["costs"] else 0
            avg_ing = sum(stats["ingredients"]) / len(stats["ingredients"]) if stats["ingredients"] else 0
            avg_steps = sum(stats["steps"]) / len(stats["steps"]) if stats["steps"] else 0
            lines.append(f"| {name} | {avg_time:.2f}s | ${avg_cost:.4f} | {avg_ing:.1f} | {avg_steps:.1f} |")

    lines.append("")
    return "\n".join(lines)


def generate_csv_report(
    video_results: Dict[str, Dict[str, BenchmarkResult]],
    photo_results: Dict[str, Dict[str, BenchmarkResult]]
) -> str:
    """Generate CSV report"""
    output = []

    # Header
    header = [
        "source_type", "source", "strategy", "success", "total_time_seconds",
        "tokens", "cost_usd", "ingredient_count", "instruction_count",
        "has_title", "has_description", "has_servings", "error_message"
    ]
    output.append(",".join(header))

    # Video results
    for url, strategies in video_results.items():
        for name, result in strategies.items():
            row = [
                "video",
                url,
                name,
                str(result.success),
                f"{result.total_time_seconds:.2f}",
                str(result.cost.openai_total_tokens if result.cost else ""),
                f"{result.cost.total_cost_usd:.4f}" if result.cost else "",
                str(result.quality.ingredient_count if result.quality else ""),
                str(result.quality.instruction_count if result.quality else ""),
                str(result.quality.has_title if result.quality else ""),
                str(result.quality.has_description if result.quality else ""),
                str(result.quality.has_servings if result.quality else ""),
                result.error_message or ""
            ]
            output.append(",".join(row))

    # Photo results
    for path, strategies in photo_results.items():
        for name, result in strategies.items():
            row = [
                "photo",
                path,
                name,
                str(result.success),
                f"{result.total_time_seconds:.2f}",
                str(result.cost.openai_total_tokens if result.cost else ""),
                f"{result.cost.total_cost_usd:.4f}" if result.cost else "",
                str(result.quality.ingredient_count if result.quality else ""),
                str(result.quality.instruction_count if result.quality else ""),
                str(result.quality.has_title if result.quality else ""),
                str(result.quality.has_description if result.quality else ""),
                str(result.quality.has_servings if result.quality else ""),
                result.error_message or ""
            ]
            output.append(",".join(row))

    return "\n".join(output)


# =============================================================================
# OUTPUT MANAGEMENT
# =============================================================================

def save_reports(
    video_results: Dict[str, Dict[str, BenchmarkResult]],
    photo_results: Dict[str, Dict[str, BenchmarkResult]],
    output_dir: Path,
    formats: List[str]
):
    """Save all reports to output directory"""
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = output_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving reports to: {run_dir}")

    # Save JSON
    if "json" in formats or "all" in formats:
        json_report = generate_json_report(video_results, photo_results)
        json_path = run_dir / "results.json"
        with open(json_path, "w") as f:
            json.dump(json_report, f, indent=2, default=str)
        print(f"  - JSON: {json_path}")

    # Save Markdown
    if "markdown" in formats or "all" in formats:
        md_report = generate_markdown_report(video_results, photo_results)
        md_path = run_dir / "report.md"
        with open(md_path, "w") as f:
            f.write(md_report)
        print(f"  - Markdown: {md_path}")

    # Save CSV
    if "csv" in formats or "all" in formats:
        csv_report = generate_csv_report(video_results, photo_results)
        csv_path = run_dir / "results.csv"
        with open(csv_path, "w") as f:
            f.write(csv_report)
        print(f"  - CSV: {csv_path}")

    # Save individual recipe JSONs
    recipes_dir = run_dir / "recipes"
    recipes_dir.mkdir(exist_ok=True)

    for url, strategies in video_results.items():
        # Create safe filename from URL
        safe_name = url.split("/")[-1][:30] or "video"
        safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)
        video_dir = recipes_dir / f"video_{safe_name}"
        video_dir.mkdir(exist_ok=True)

        for name, result in strategies.items():
            if result.success and result.recipe_data:
                recipe_path = video_dir / f"{name}.json"
                with open(recipe_path, "w") as f:
                    json.dump(result.recipe_data, f, indent=2)

    for path, strategies in photo_results.items():
        safe_name = Path(path).stem[:30]
        safe_name = "".join(c if c.isalnum() else "_" for c in safe_name)
        photo_dir = recipes_dir / f"photo_{safe_name}"
        photo_dir.mkdir(exist_ok=True)

        for name, result in strategies.items():
            if result.success and result.recipe_data:
                recipe_path = photo_dir / f"{name}.json"
                with open(recipe_path, "w") as f:
                    json.dump(result.recipe_data, f, indent=2)

    print(f"  - Recipes: {recipes_dir}")

    return run_dir


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Benchmark recipe extraction strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with config file
  python scripts/benchmark_extraction_full.py --config benchmark_inputs/config.json

  # Test specific video
  python scripts/benchmark_extraction_full.py --video "https://tiktok.com/..." --video-strategies full,no_ocr

  # Test specific photo
  python scripts/benchmark_extraction_full.py --photo "path/to/image.jpg" --photo-strategies full,ocr_only,vision_only

  # Multiple inputs
  python scripts/benchmark_extraction_full.py --video "url1" --video "url2" --photo "image.jpg"
        """
    )

    # Input sources
    parser.add_argument("--config", type=Path, help="Config JSON file with video_urls and photo_paths")
    parser.add_argument("--video", action="append", dest="videos", help="Video URL to test (can specify multiple)")
    parser.add_argument("--photo", action="append", dest="photos", help="Photo path to test (can specify multiple)")

    # Strategy selection
    parser.add_argument(
        "--video-strategies",
        default="full,no_ocr,description_only,transcript_only",
        help="Comma-separated video strategies (default: full,no_ocr,description_only,transcript_only)"
    )
    parser.add_argument(
        "--photo-strategies",
        default="full,ocr_only,vision_only",
        help="Comma-separated photo strategies (default: full,ocr_only,vision_only)"
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--format",
        default="all",
        help="Output formats: json, markdown, csv, all (default: all)"
    )

    # Verbosity
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Collect inputs
    video_urls = args.videos or []
    photo_paths = args.photos or []
    video_strategies = args.video_strategies.split(",")
    photo_strategies = args.photo_strategies.split(",")

    # Load config if provided
    if args.config:
        if args.config.exists():
            with open(args.config) as f:
                config = json.load(f)
            video_urls.extend(config.get("video_urls", []))
            photo_paths.extend(config.get("photo_paths", []))
            if "video_strategies" in config:
                video_strategies = config["video_strategies"]
            if "photo_strategies" in config:
                photo_strategies = config["photo_strategies"]
        else:
            print(f"Warning: Config file not found: {args.config}")

    # Validate inputs
    if not video_urls and not photo_paths:
        print("Error: No inputs specified. Use --video, --photo, or --config")
        print("Use --help for usage information")
        return

    # Print configuration
    print("=" * 60)
    print("Recipe Extraction Benchmark")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Video URLs: {len(video_urls)}")
    print(f"Photo paths: {len(photo_paths)}")
    print(f"Video strategies: {', '.join(video_strategies)}")
    print(f"Photo strategies: {', '.join(photo_strategies)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Output formats: {args.format}")

    # Initialize services
    openai_service = OpenAIService()

    # Run benchmarks
    video_results = {}
    photo_results = {}

    if video_urls:
        video_results = await run_video_benchmarks(video_urls, video_strategies, openai_service)

    if photo_paths:
        photo_results = await run_photo_benchmarks(photo_paths, photo_strategies, openai_service)

    # Save reports
    formats = args.format.split(",")
    run_dir = save_reports(video_results, photo_results, args.output_dir, formats)

    # Print summary
    print("\n" + "=" * 60)
    print("Benchmark Complete!")
    print("=" * 60)

    total_success = sum(
        1 for strategies in list(video_results.values()) + list(photo_results.values())
        for result in strategies.values() if result.success
    )
    total_failed = sum(
        1 for strategies in list(video_results.values()) + list(photo_results.values())
        for result in strategies.values() if not result.success
    )
    print(f"Results: {total_success} successful, {total_failed} failed")
    print(f"Reports saved to: {run_dir}")


if __name__ == "__main__":
    asyncio.run(main())
