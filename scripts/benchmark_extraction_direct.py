#!/usr/bin/env python3
"""
Direct benchmark script for comparing recipe extraction methods.
Runs the extraction directly without needing the server.

Compares:
1. With Image: OCR + GPT-4o-mini with image (current production)
2. OCR-Only: OCR + GPT-4o-mini with only OCR text

Usage:
    cd cuistudio-server
    source venv/bin/activate
    python scripts/benchmark_extraction_direct.py
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add the app to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.openai_service import OpenAIService
from app.services.extractors.photo_extractor import PhotoExtractor

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent  # recipe-app/

# Test images (relative to project root)
TEST_IMAGES = [
    "TEST_IMAGE.jpeg",
    "TEST_IMAGE2.jpeg",
    "TEST_IMAGE3.jpeg",
    "TEST_IMAGE4.jpeg",
    "TEST_IMAGE5.jpeg",
]

OUTPUT_FILE = Path(__file__).parent.parent / "benchmark_results.md"


def format_ingredients(ingredients: List[Dict]) -> str:
    """Format ingredients list for markdown output"""
    if not ingredients:
        return "_No ingredients extracted_"

    lines = []
    current_group = None

    for ing in ingredients:
        group = ing.get("group")
        if group and group != current_group:
            lines.append(f"\n**{group}**")
            current_group = group

        qty = ing.get("quantity", "")
        unit = ing.get("unit", "")
        name = ing.get("name", "Unknown")
        notes = ing.get("notes", "")

        # Build ingredient string
        parts = []
        if qty:
            parts.append(str(qty))
        if unit:
            parts.append(unit)
        parts.append(name)

        line = " ".join(parts)
        if notes:
            line += f" ({notes})"

        lines.append(f"- {line}")

    return "\n".join(lines)


def format_instructions(instructions: List[Dict]) -> str:
    """Format instructions list for markdown output"""
    if not instructions:
        return "_No instructions extracted_"

    lines = []
    current_group = None

    for inst in instructions:
        group = inst.get("group")
        if group and group != current_group:
            lines.append(f"\n**{group}**")
            current_group = group

        step_num = inst.get("step_number", "?")
        title = inst.get("title", "")
        description = inst.get("description", "")
        timer = inst.get("timer_minutes")

        line = f"{step_num}. "
        if title:
            line += f"**{title}**: "
        line += description
        if timer:
            line += f" _(~{timer} min)_"

        lines.append(line)

    return "\n".join(lines)


def format_recipe_section(result: Dict[str, Any], method_name: str) -> str:
    """Format a single recipe result section"""
    lines = []
    lines.append(f"### Method: {method_name}")
    lines.append("")

    # Check for error
    if "error" in result:
        lines.append(f"**ERROR**: {result['error']}")
        lines.append("")
        return "\n".join(lines)

    # Basic info
    title = result.get("title", "Unknown")
    description = result.get("description", "")

    lines.append(f"**Title**: {title}")
    if description:
        lines.append(f"**Description**: {description}")

    # Stats
    stats = result.get("_extraction_stats", {})
    benchmark = result.get("_benchmark", {})

    tokens = stats.get("total_tokens", "N/A")
    cost = stats.get("estimated_cost_usd", 0)
    extraction_time = benchmark.get("extraction_time_seconds", "N/A")

    if isinstance(extraction_time, (int, float)):
        lines.append(f"**Tokens**: {tokens} | **Cost**: ${cost:.4f} | **Time**: {extraction_time:.2f}s")
    else:
        lines.append(f"**Tokens**: {tokens} | **Cost**: ${cost:.4f} | **Time**: {extraction_time}")
    lines.append("")

    # Metadata
    servings = result.get("servings", "N/A")
    difficulty = result.get("difficulty", "N/A")
    prep_time = result.get("prep_time_minutes", "N/A")
    cook_time = result.get("cook_time_minutes", "N/A")
    total_time = result.get("total_time_minutes", "N/A")

    lines.append(f"**Servings**: {servings} | **Difficulty**: {difficulty}")
    lines.append(f"**Prep**: {prep_time} min | **Cook**: {cook_time} min | **Total**: {total_time} min")
    lines.append("")

    # Ingredients
    lines.append("#### Ingredients")
    lines.append(format_ingredients(result.get("ingredients", [])))
    lines.append("")

    # Instructions
    lines.append("#### Instructions")
    lines.append(format_instructions(result.get("instructions", [])))
    lines.append("")

    return "\n".join(lines)


async def run_benchmark_for_image(
    openai_service: OpenAIService,
    photo_extractor: PhotoExtractor,
    image_path: str
) -> Dict[str, Any]:
    """Run benchmark for a single image"""
    print(f"  Benchmarking: {Path(image_path).name}")

    result = {
        "image_path": image_path,
        "ocr_text": "",
        "with_image": {},
        "ocr_only": {}
    }

    try:
        # Step 1: Run OCR (shared between both methods)
        print("    Running OCR...")
        ocr_start = time.time()
        ocr_text = await photo_extractor._run_ocr(image_path)
        ocr_time = time.time() - ocr_start
        result["ocr_text"] = ocr_text
        print(f"    OCR: {ocr_time:.2f}s, {len(ocr_text)} chars")

        # Step 2: Method A - With Image
        print("    Running WITH IMAGE extraction...")
        with_image_start = time.time()
        try:
            with_image_result = await openai_service.extract_recipe_from_image_with_ocr(
                image_path,
                ocr_text
            )
            with_image_time = time.time() - with_image_start
            with_image_result["_benchmark"] = {
                "extraction_time_seconds": with_image_time,
                "ocr_time_seconds": ocr_time,
                "total_time_seconds": ocr_time + with_image_time
            }
            result["with_image"] = with_image_result
            print(f"    With Image: {with_image_time:.2f}s, {with_image_result.get('_extraction_stats', {}).get('total_tokens', 'N/A')} tokens")
        except Exception as e:
            with_image_time = time.time() - with_image_start
            result["with_image"] = {
                "error": str(e),
                "_benchmark": {
                    "extraction_time_seconds": with_image_time,
                    "ocr_time_seconds": ocr_time
                }
            }
            print(f"    With Image FAILED: {e}")

        # Step 3: Method B - OCR Only
        print("    Running OCR-ONLY extraction...")
        ocr_only_start = time.time()
        try:
            ocr_only_result = await openai_service.extract_recipe_from_ocr_text_only(ocr_text)
            ocr_only_time = time.time() - ocr_only_start
            ocr_only_result["_benchmark"] = {
                "extraction_time_seconds": ocr_only_time,
                "ocr_time_seconds": ocr_time,
                "total_time_seconds": ocr_time + ocr_only_time
            }
            result["ocr_only"] = ocr_only_result
            print(f"    OCR-Only: {ocr_only_time:.2f}s, {ocr_only_result.get('_extraction_stats', {}).get('total_tokens', 'N/A')} tokens")
        except Exception as e:
            ocr_only_time = time.time() - ocr_only_start
            result["ocr_only"] = {
                "error": str(e),
                "_benchmark": {
                    "extraction_time_seconds": ocr_only_time,
                    "ocr_time_seconds": ocr_time
                }
            }
            print(f"    OCR-Only FAILED: {e}")

        print("    ✓ Complete")

    except Exception as e:
        print(f"    ✗ Failed: {e}")
        result["error"] = str(e)

    return result


async def main():
    """Main benchmark runner"""
    print("=" * 60)
    print("Recipe Extraction Benchmark (Direct)")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Testing {len(TEST_IMAGES)} images")
    print("")

    # Initialize services
    openai_service = OpenAIService()
    photo_extractor = PhotoExtractor()

    results = []
    summary_stats = {
        "with_image": {"tokens": [], "cost": [], "time": []},
        "ocr_only": {"tokens": [], "cost": [], "time": []}
    }

    for image_name in TEST_IMAGES:
        image_path = str(PROJECT_ROOT / image_name)

        if not os.path.exists(image_path):
            print(f"  SKIP: {image_name} not found")
            continue

        result = await run_benchmark_for_image(openai_service, photo_extractor, image_path)
        results.append(result)

        # Collect stats for summary
        if "error" not in result:
            wi = result.get("with_image", {})
            oo = result.get("ocr_only", {})

            if "_extraction_stats" in wi and "error" not in wi:
                summary_stats["with_image"]["tokens"].append(wi["_extraction_stats"].get("total_tokens", 0))
                summary_stats["with_image"]["cost"].append(wi["_extraction_stats"].get("estimated_cost_usd", 0))
                summary_stats["with_image"]["time"].append(wi["_benchmark"].get("extraction_time_seconds", 0))

            if "_extraction_stats" in oo and "error" not in oo:
                summary_stats["ocr_only"]["tokens"].append(oo["_extraction_stats"].get("total_tokens", 0))
                summary_stats["ocr_only"]["cost"].append(oo["_extraction_stats"].get("estimated_cost_usd", 0))
                summary_stats["ocr_only"]["time"].append(oo["_benchmark"].get("extraction_time_seconds", 0))

        print("")

    # Generate markdown report
    print("Generating report...")

    report_lines = []
    report_lines.append("# Recipe Extraction Benchmark Results")
    report_lines.append("")
    report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("## Summary")
    report_lines.append("")

    # Calculate averages
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0

    wi_avg_tokens = avg(summary_stats["with_image"]["tokens"])
    wi_avg_cost = avg(summary_stats["with_image"]["cost"])
    wi_avg_time = avg(summary_stats["with_image"]["time"])

    oo_avg_tokens = avg(summary_stats["ocr_only"]["tokens"])
    oo_avg_cost = avg(summary_stats["ocr_only"]["cost"])
    oo_avg_time = avg(summary_stats["ocr_only"]["time"])

    token_savings_pct = ((wi_avg_tokens - oo_avg_tokens) / wi_avg_tokens * 100) if wi_avg_tokens else 0
    cost_savings_pct = ((wi_avg_cost - oo_avg_cost) / wi_avg_cost * 100) if wi_avg_cost else 0
    time_savings_pct = ((wi_avg_time - oo_avg_time) / wi_avg_time * 100) if wi_avg_time else 0

    report_lines.append("| Metric | With Image (avg) | OCR-Only (avg) | Savings |")
    report_lines.append("|--------|------------------|----------------|---------|")
    report_lines.append(f"| Tokens | {wi_avg_tokens:.0f} | {oo_avg_tokens:.0f} | {wi_avg_tokens - oo_avg_tokens:.0f} ({token_savings_pct:.1f}%) |")
    report_lines.append(f"| Cost | ${wi_avg_cost:.4f} | ${oo_avg_cost:.4f} | ${wi_avg_cost - oo_avg_cost:.4f} ({cost_savings_pct:.1f}%) |")
    report_lines.append(f"| Time | {wi_avg_time:.2f}s | {oo_avg_time:.2f}s | {wi_avg_time - oo_avg_time:.2f}s ({time_savings_pct:.1f}%) |")
    report_lines.append("")

    # Individual results
    for i, result in enumerate(results, 1):
        image_name = Path(result.get("image_path", f"Image {i}")).name

        report_lines.append("---")
        report_lines.append("")
        report_lines.append(f"## Recipe {i}: {image_name}")
        report_lines.append("")

        if "error" in result and "with_image" not in result:
            report_lines.append(f"**ERROR**: {result['error']}")
            report_lines.append("")
            continue

        # OCR text preview
        ocr_text = result.get("ocr_text", "")
        if ocr_text:
            report_lines.append("<details>")
            report_lines.append("<summary>OCR Text Preview (click to expand)</summary>")
            report_lines.append("")
            report_lines.append("```")
            report_lines.append(ocr_text[:1500])
            if len(ocr_text) > 1500:
                report_lines.append("... (truncated)")
            report_lines.append("```")
            report_lines.append("</details>")
            report_lines.append("")

        # With Image result
        with_image = result.get("with_image", {})
        report_lines.append(format_recipe_section(with_image, "With Image"))

        report_lines.append("---")
        report_lines.append("")

        # OCR Only result
        ocr_only = result.get("ocr_only", {})
        report_lines.append(format_recipe_section(ocr_only, "OCR-Only"))

    # Write report
    report_content = "\n".join(report_lines)
    OUTPUT_FILE.write_text(report_content)

    print(f"Report saved to: {OUTPUT_FILE}")
    print("")
    print("=" * 60)
    print("Benchmark Complete!")
    print("=" * 60)
    print(f"  With Image: avg {wi_avg_tokens:.0f} tokens, ${wi_avg_cost:.4f}, {wi_avg_time:.2f}s")
    print(f"  OCR-Only:   avg {oo_avg_tokens:.0f} tokens, ${oo_avg_cost:.4f}, {oo_avg_time:.2f}s")
    print(f"  Savings:    {wi_avg_tokens - oo_avg_tokens:.0f} tokens ({token_savings_pct:.1f}%), ${wi_avg_cost - oo_avg_cost:.4f} ({cost_savings_pct:.1f}%), {wi_avg_time - oo_avg_time:.2f}s ({time_savings_pct:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
