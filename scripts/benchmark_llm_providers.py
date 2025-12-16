#!/usr/bin/env python3
"""
Benchmark LLM providers for recipe extraction speed, cost, and quality.

Uses the ACTUAL production prompts from openai_service.py and tests against
real recipe images from benchmark_inputs/.

Tests:
1. OpenAI GPT-4o-mini (current production)
2. OpenAI GPT-4o (higher quality)
3. Google Gemini 2.0/2.5 Flash variants (fast, cheap)
4. Anthropic Claude 3.5 Haiku (fast)

Usage:
    cd cuistudio-server
    source venv/bin/activate
    python scripts/benchmark_llm_providers.py
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add the app to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.core.config import get_settings

settings = get_settings()


# =============================================================================
# PRODUCTION PROMPT (from openai_service.py extract_recipe_from_ocr_text_only)
# =============================================================================

SYSTEM_PROMPT = """You are a professional recipe extraction expert.

STEP 1 - CONTENT CLASSIFICATION:
Analyze the OCR text to determine what type of content this is:
- "recipe_card": Recipe text with ingredients and/or instructions
- "non_food": Not food-related content

STEP 2 - EXTRACTION:

If "recipe_card":
- Extract the recipe from the OCR text
- Fix common OCR errors: misread characters (0/O, 1/l/I), merged words, spacing issues
- Structure into proper recipe format

If "non_food":
- Return is_recipe: false with a rejection reason

EXTRACTION RULES (for recipe_card):
1. Extract COMPLETE ingredients: quantity + unit + name (e.g., "2 cups flour" not "2 cups")
2. Group ingredients logically based on recipe sections:
   - "For the [main dish]" - main ingredients (e.g., "For the soup", "For the duck")
   - "For the [sauce/topping]" - sauce or topping ingredients
   - "For the garnish" - garnish/decoration ingredients
   - "To taste" - salt, pepper, and seasonings added to preference
   - If no logical groups exist, use null for the group field
3. Number all instruction steps sequentially
4. Each instruction should have a concise title and detailed description
5. Group instructions logically based on recipe sections
6. ESTIMATE cooking time for EACH step based on the action
7. If servings not visible, estimate based on ingredient quantities
8. Return ONLY valid JSON, no markdown formatting

Response format:
{
    "content_type": "recipe_card" | "non_food",
    "is_recipe": true or false,
    "rejection_reason": "Brief explanation (if non_food)",

    // Only include these if is_recipe=true:
    "title": "Recipe name",
    "description": "Brief description of the dish",
    "ingredients": [
        {"name": "ingredient name", "quantity": 2.0, "unit": "cups", "notes": "optional prep notes", "group": "For the soup"}
    ],
    "instructions": [
        {"step_number": 1, "title": "Step title", "description": "Detailed instruction text", "timer_minutes": 5, "group": "For the soup"}
    ],
    "servings": 4,
    "difficulty": "easy|medium|hard",
    "tags": ["tag1", "tag2"],
    "categories": ["category1"],
    "prep_time_minutes": 15,
    "cook_time_minutes": 30,
    "total_time_minutes": 45
}"""


def get_user_prompt(ocr_text: str) -> str:
    """Generate the user prompt with OCR text (matches production)"""
    return f"""Extract a recipe from this OCR text (may contain OCR errors that need fixing):

---OCR TEXT---
{ocr_text}
---END OCR---

Task:
1. First, classify if this is recipe content or not
2. If recipe: Extract and structure the recipe, fixing any OCR errors
3. If not recipe: Return is_recipe: false with rejection reason
4. Return structured JSON following the specified format"""


@dataclass
class BenchmarkResult:
    provider: str
    model: str
    image_name: str
    success: bool
    latency_seconds: float
    time_to_first_token: Optional[float]
    tokens_per_second: Optional[float]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    ingredient_count: int
    instruction_count: int
    recipe_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Pricing per 1M tokens (Dec 2024)
PRICING = {
    # OpenAI
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    # Google Gemini
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.5-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
    # Anthropic Claude
    "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost based on token usage"""
    if model not in PRICING:
        return 0.0
    prices = PRICING[model]
    return (input_tokens / 1_000_000) * prices["input"] + (output_tokens / 1_000_000) * prices["output"]


# =============================================================================
# OCR Functions
# =============================================================================

# Register HEIF/HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    print("HEIC/HEIF support enabled via pillow-heif")
except ImportError:
    print("Warning: pillow-heif not installed, HEIC images may not be readable")


def run_ocr(image_path: str) -> str:
    """Run Tesseract OCR on an image with enhanced preprocessing"""
    import pytesseract
    from PIL import Image, ImageEnhance

    try:
        image = Image.open(image_path)

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # UPSCALE small images (OCR works best around 300 DPI)
        min_dimension = 2000
        if min(image.size) < min_dimension:
            ratio = min_dimension / min(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Downscale very large images to avoid memory issues
        max_dimension = 4000
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Strong contrast enhancement (2.0) for crisp text edges
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Strong sharpening (2.0) for better character definition
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)

        # Slight brightness increase (1.1) helps with dark text
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)

        # Run OCR with optimized settings
        # PSM 3 = Fully automatic page segmentation (better for mixed layouts)
        # OEM 3 = Default, combines legacy + LSTM neural network
        custom_config = r'--oem 3 --psm 3'
        text = pytesseract.image_to_string(image, config=custom_config)

        return text.strip()

    except Exception as e:
        print(f"Error running OCR: {e}")
        return ""


# =============================================================================
# LLM Benchmark Functions
# =============================================================================

async def benchmark_openai(model: str, ocr_text: str, image_name: str) -> BenchmarkResult:
    """Benchmark OpenAI models"""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        organization=settings.OPENAI_ORGANIZATION_ID,
        project=settings.OPENAI_PROJECT_ID
    )

    user_prompt = get_user_prompt(ocr_text)
    start_time = time.time()
    first_token_time = None

    try:
        # Use streaming to measure TTFT
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            stream=True
        )

        content = ""
        async for chunk in response:
            if first_token_time is None and chunk.choices[0].delta.content:
                first_token_time = time.time() - start_time
            if chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content

        end_time = time.time()
        latency = end_time - start_time

        # Parse result
        result = json.loads(content)
        ingredient_count = len(result.get("ingredients", []))
        instruction_count = len(result.get("instructions", []))

        # Get token counts from a non-streaming call for accurate count
        usage_response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1
        )
        input_tokens = usage_response.usage.prompt_tokens
        output_tokens = len(content) // 4  # Estimate

        tokens_per_second = output_tokens / (latency - (first_token_time or 0)) if latency > (first_token_time or 0) else 0

        return BenchmarkResult(
            provider="OpenAI",
            model=model,
            image_name=image_name,
            success=True,
            latency_seconds=latency,
            time_to_first_token=first_token_time,
            tokens_per_second=tokens_per_second,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=calculate_cost(model, input_tokens, output_tokens),
            ingredient_count=ingredient_count,
            instruction_count=instruction_count,
            recipe_data=result
        )

    except Exception as e:
        return BenchmarkResult(
            provider="OpenAI",
            model=model,
            image_name=image_name,
            success=False,
            latency_seconds=time.time() - start_time,
            time_to_first_token=None,
            tokens_per_second=None,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0,
            ingredient_count=0,
            instruction_count=0,
            error=str(e)
        )


async def benchmark_gemini(model: str, ocr_text: str, image_name: str) -> BenchmarkResult:
    """Benchmark Google Gemini models"""
    import google.generativeai as genai

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return BenchmarkResult(
            provider="Google",
            model=model,
            image_name=image_name,
            success=False,
            latency_seconds=0,
            time_to_first_token=None,
            tokens_per_second=None,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0,
            ingredient_count=0,
            instruction_count=0,
            error="GOOGLE_API_KEY not set"
        )

    genai.configure(api_key=api_key)

    user_prompt = get_user_prompt(ocr_text)
    start_time = time.time()
    first_token_time = None

    try:
        # Configure model
        generation_config = genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json"
        )

        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=SYSTEM_PROMPT
        )

        # Use streaming
        response = gemini_model.generate_content(
            user_prompt,
            stream=True
        )

        content = ""
        for chunk in response:
            if first_token_time is None and chunk.text:
                first_token_time = time.time() - start_time
            if chunk.text:
                content += chunk.text

        end_time = time.time()
        latency = end_time - start_time

        # Parse result
        result = json.loads(content)
        ingredient_count = len(result.get("ingredients", []))
        instruction_count = len(result.get("instructions", []))

        # Get token counts
        input_tokens = gemini_model.count_tokens(SYSTEM_PROMPT + user_prompt).total_tokens
        output_tokens = len(content) // 4  # Estimate

        tokens_per_second = output_tokens / (latency - (first_token_time or 0)) if latency > (first_token_time or 0) else 0

        return BenchmarkResult(
            provider="Google",
            model=model,
            image_name=image_name,
            success=True,
            latency_seconds=latency,
            time_to_first_token=first_token_time,
            tokens_per_second=tokens_per_second,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=calculate_cost(model, input_tokens, output_tokens),
            ingredient_count=ingredient_count,
            instruction_count=instruction_count,
            recipe_data=result
        )

    except Exception as e:
        return BenchmarkResult(
            provider="Google",
            model=model,
            image_name=image_name,
            success=False,
            latency_seconds=time.time() - start_time,
            time_to_first_token=None,
            tokens_per_second=None,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0,
            ingredient_count=0,
            instruction_count=0,
            recipe_data=None,
            error=str(e)
        )


async def benchmark_anthropic(model: str, ocr_text: str, image_name: str) -> BenchmarkResult:
    """Benchmark Anthropic Claude models"""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return BenchmarkResult(
            provider="Anthropic",
            model=model,
            image_name=image_name,
            success=False,
            latency_seconds=0,
            time_to_first_token=None,
            tokens_per_second=None,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0,
            ingredient_count=0,
            instruction_count=0,
            error="ANTHROPIC_API_KEY not set"
        )

    client = anthropic.AsyncAnthropic(api_key=api_key)

    user_prompt = get_user_prompt(ocr_text)
    start_time = time.time()
    first_token_time = None

    try:
        # Use streaming
        content = ""
        async with client.messages.stream(
            model=model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            async for text in stream.text_stream:
                if first_token_time is None and text:
                    first_token_time = time.time() - start_time
                content += text

        end_time = time.time()
        latency = end_time - start_time

        # Get final message for token counts
        message = await stream.get_final_message()
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens

        # Parse result
        result = json.loads(content)
        ingredient_count = len(result.get("ingredients", []))
        instruction_count = len(result.get("instructions", []))

        tokens_per_second = output_tokens / (latency - (first_token_time or 0)) if latency > (first_token_time or 0) else 0

        return BenchmarkResult(
            provider="Anthropic",
            model=model,
            image_name=image_name,
            success=True,
            latency_seconds=latency,
            time_to_first_token=first_token_time,
            tokens_per_second=tokens_per_second,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=calculate_cost(model, input_tokens, output_tokens),
            ingredient_count=ingredient_count,
            instruction_count=instruction_count,
            recipe_data=result
        )

    except Exception as e:
        return BenchmarkResult(
            provider="Anthropic",
            model=model,
            image_name=image_name,
            success=False,
            latency_seconds=time.time() - start_time,
            time_to_first_token=None,
            tokens_per_second=None,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0,
            ingredient_count=0,
            instruction_count=0,
            recipe_data=None,
            error=str(e)
        )


# =============================================================================
# Main Benchmark Runner
# =============================================================================

async def run_benchmarks(image_ocr_pairs: List[tuple]) -> List[BenchmarkResult]:
    """Run all benchmarks for all images"""
    models = [
        # OpenAI
        ("openai", "gpt-4o-mini"),
        ("openai", "gpt-4o"),
        # Google Gemini (newest first)
        ("gemini", "gemini-2.5-flash"),
        ("gemini", "gemini-2.5-flash-lite"),
        ("gemini", "gemini-2.0-flash"),
        ("gemini", "gemini-2.0-flash-lite"),
        # Anthropic Claude
        ("anthropic", "claude-3-5-haiku-latest"),
    ]

    all_results = []

    for image_name, ocr_text in image_ocr_pairs:
        print(f"\n{'='*70}")
        print(f"Testing image: {image_name}")
        print(f"OCR text length: {len(ocr_text)} chars")
        print("=" * 70)

        for provider, model in models:
            print(f"\n  {provider.upper()} - {model}...", end=" ", flush=True)

            if provider == "openai":
                result = await benchmark_openai(model, ocr_text, image_name)
            elif provider == "gemini":
                result = await benchmark_gemini(model, ocr_text, image_name)
            elif provider == "anthropic":
                result = await benchmark_anthropic(model, ocr_text, image_name)

            all_results.append(result)

            if result.success:
                print(f"✓ {result.latency_seconds:.2f}s | {result.ingredient_count} ing | {result.instruction_count} steps")
            else:
                print(f"✗ {result.error}")

            # Small delay between API calls
            await asyncio.sleep(0.5)

    return all_results


def print_summary(results: List[BenchmarkResult]):
    """Print summary table grouped by model"""
    print("\n" + "=" * 100)
    print("BENCHMARK SUMMARY BY MODEL")
    print("=" * 100)

    # Group results by model
    from collections import defaultdict
    by_model = defaultdict(list)
    for r in results:
        if r.success:
            by_model[r.model].append(r)

    # Calculate averages per model
    model_stats = []
    for model, model_results in by_model.items():
        avg_latency = sum(r.latency_seconds for r in model_results) / len(model_results)
        avg_ttft = sum(r.time_to_first_token for r in model_results if r.time_to_first_token) / len([r for r in model_results if r.time_to_first_token]) if any(r.time_to_first_token for r in model_results) else 0
        avg_cost = sum(r.cost_usd for r in model_results) / len(model_results)
        avg_ingredients = sum(r.ingredient_count for r in model_results) / len(model_results)
        avg_instructions = sum(r.instruction_count for r in model_results) / len(model_results)

        model_stats.append({
            "model": model,
            "provider": model_results[0].provider,
            "avg_latency": avg_latency,
            "avg_ttft": avg_ttft,
            "avg_cost": avg_cost,
            "avg_ingredients": avg_ingredients,
            "avg_instructions": avg_instructions,
            "count": len(model_results)
        })

    # Sort by latency
    model_stats.sort(key=lambda x: x["avg_latency"])

    print(f"\n{'Model':<30} {'Latency':>10} {'TTFT':>8} {'Cost':>12} {'Avg Ing':>10} {'Avg Steps':>10}")
    print("-" * 100)

    for stats in model_stats:
        ttft = f"{stats['avg_ttft']:.2f}s" if stats['avg_ttft'] else "N/A"
        print(f"{stats['model']:<30} {stats['avg_latency']:>8.2f}s {ttft:>8} ${stats['avg_cost']:>10.6f} {stats['avg_ingredients']:>10.1f} {stats['avg_instructions']:>10.1f}")

    # Recommendations
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)

    if model_stats:
        fastest = min(model_stats, key=lambda x: x["avg_latency"])
        cheapest = min(model_stats, key=lambda x: x["avg_cost"])

        print(f"\n  Fastest overall:    {fastest['model']} ({fastest['avg_latency']:.2f}s avg)")
        print(f"  Cheapest:           {cheapest['model']} (${cheapest['avg_cost']:.6f} avg)")

        # Best value (speed/cost ratio)
        for s in model_stats:
            s["value_score"] = (1 / s["avg_latency"]) / (s["avg_cost"] + 0.0001)
        best_value = max(model_stats, key=lambda x: x["value_score"])
        print(f"  Best value:         {best_value['model']}")


def generate_recipe_report(results: List[BenchmarkResult], output_dir: Path) -> str:
    """Generate a markdown report with full recipes for comparison"""
    lines = []
    lines.append("# LLM Recipe Extraction Comparison (Production Prompt)")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("Using actual production prompt from `openai_service.py`")
    lines.append("")

    # Group results by image
    from collections import defaultdict
    by_image = defaultdict(list)
    for r in results:
        by_image[r.image_name].append(r)

    # Summary table
    lines.append("## Summary Table (All Images)")
    lines.append("")
    lines.append("| Image | Model | Latency | TTFT | Cost | Ingredients | Steps |")
    lines.append("|-------|-------|---------|------|------|-------------|-------|")

    for image_name in sorted(by_image.keys()):
        image_results = sorted(by_image[image_name], key=lambda r: r.latency_seconds if r.success else float('inf'))
        for r in image_results:
            if r.success:
                ttft = f"{r.time_to_first_token:.2f}s" if r.time_to_first_token else "N/A"
                lines.append(f"| {image_name} | {r.model} | {r.latency_seconds:.2f}s | {ttft} | ${r.cost_usd:.4f} | {r.ingredient_count} | {r.instruction_count} |")
            else:
                lines.append(f"| {image_name} | {r.model} | FAILED | - | - | - | - |")

    lines.append("")

    # Model averages
    lines.append("## Model Averages")
    lines.append("")
    lines.append("| Model | Avg Latency | Avg Cost | Avg Ingredients | Avg Steps |")
    lines.append("|-------|-------------|----------|-----------------|-----------|")

    by_model = defaultdict(list)
    for r in results:
        if r.success:
            by_model[r.model].append(r)

    model_avgs = []
    for model, model_results in by_model.items():
        avg_latency = sum(r.latency_seconds for r in model_results) / len(model_results)
        avg_cost = sum(r.cost_usd for r in model_results) / len(model_results)
        avg_ingredients = sum(r.ingredient_count for r in model_results) / len(model_results)
        avg_instructions = sum(r.instruction_count for r in model_results) / len(model_results)
        model_avgs.append((model, avg_latency, avg_cost, avg_ingredients, avg_instructions))

    model_avgs.sort(key=lambda x: x[1])  # Sort by latency
    for model, avg_lat, avg_cost, avg_ing, avg_steps in model_avgs:
        lines.append(f"| {model} | {avg_lat:.2f}s | ${avg_cost:.4f} | {avg_ing:.1f} | {avg_steps:.1f} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Full recipes per image
    lines.append("## Full Recipe Comparison by Image")
    lines.append("")

    for image_name in sorted(by_image.keys()):
        lines.append(f"### {image_name}")
        lines.append("")

        image_results = sorted(by_image[image_name], key=lambda r: r.latency_seconds if r.success else float('inf'))

        for r in image_results:
            lines.append(f"#### {r.model}")
            lines.append("")
            lines.append(f"**Provider**: {r.provider} | **Latency**: {r.latency_seconds:.2f}s | **Cost**: ${r.cost_usd:.4f}")
            lines.append("")

            if r.success and r.recipe_data:
                recipe = r.recipe_data

                # Check if it's a recipe
                if not recipe.get("is_recipe", True):
                    lines.append(f"**Not a recipe**: {recipe.get('rejection_reason', 'Unknown')}")
                    lines.append("")
                else:
                    lines.append(f"**Title**: {recipe.get('title', 'N/A')}")
                    lines.append("")
                    lines.append(f"**Description**: {recipe.get('description', 'N/A')}")
                    lines.append("")

                    # Metadata
                    servings = recipe.get('servings', 'N/A')
                    difficulty = recipe.get('difficulty', 'N/A')
                    prep = recipe.get('prep_time_minutes', 'N/A')
                    cook = recipe.get('cook_time_minutes', 'N/A')
                    total = recipe.get('total_time_minutes', 'N/A')
                    lines.append(f"**Servings**: {servings} | **Difficulty**: {difficulty} | **Prep**: {prep} min | **Cook**: {cook} min | **Total**: {total} min")
                    lines.append("")

                    # Ingredients
                    lines.append("**Ingredients:**")
                    lines.append("")
                    ingredients = recipe.get('ingredients', [])
                    current_group = None
                    for ing in ingredients:
                        group = ing.get('group')
                        if group and group != current_group:
                            lines.append(f"\n*{group}*")
                            current_group = group

                        qty = ing.get('quantity', '')
                        unit = ing.get('unit', '')
                        name = ing.get('name', '')
                        notes = ing.get('notes', '')

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

                    lines.append("")

                    # Instructions
                    lines.append("**Instructions:**")
                    lines.append("")
                    instructions = recipe.get('instructions', [])
                    current_group = None
                    for inst in instructions:
                        group = inst.get('group')
                        if group and group != current_group:
                            lines.append(f"\n*{group}*")
                            current_group = group

                        step = inst.get('step_number', '?')
                        title = inst.get('title', '')
                        desc = inst.get('description', '')
                        timer = inst.get('timer_minutes')

                        line = f"{step}. "
                        if title:
                            line += f"**{title}**: "
                        line += desc
                        if timer:
                            line += f" _(~{timer} min)_"
                        lines.append(line)

                    lines.append("")

                    # Tags
                    tags = recipe.get('tags', [])
                    categories = recipe.get('categories', [])
                    if tags or categories:
                        lines.append(f"**Tags**: {', '.join(tags) if tags else 'N/A'} | **Categories**: {', '.join(categories) if categories else 'N/A'}")
                        lines.append("")

            elif not r.success:
                lines.append(f"**Error**: {r.error}")
                lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


async def main():
    print("=" * 100)
    print("LLM Provider Benchmark for Recipe Extraction (Production Prompt)")
    print("=" * 100)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    # Check for API keys
    print("API Keys configured:")
    print(f"  OpenAI: {'✓' if settings.OPENAI_API_KEY else '✗'}")
    print(f"  Google: {'✓' if os.environ.get('GOOGLE_API_KEY') else '✗'}")
    print(f"  Anthropic: {'✓' if os.environ.get('ANTHROPIC_API_KEY') else '✗'}")

    # Find benchmark images
    benchmark_dir = Path(__file__).parent.parent / "benchmark_inputs"
    image_extensions = {'.heic', '.jpg', '.jpeg', '.png', '.webp'}
    image_files = [f for f in benchmark_dir.iterdir() if f.suffix.lower() in image_extensions]

    if not image_files:
        print(f"\nNo images found in {benchmark_dir}")
        print("Please add test images to the benchmark_inputs directory.")
        return

    print(f"\nFound {len(image_files)} test images:")
    for f in image_files:
        print(f"  - {f.name}")

    # Run OCR on all images first
    print("\n" + "=" * 100)
    print("RUNNING OCR ON ALL IMAGES")
    print("=" * 100)

    image_ocr_pairs = []
    for image_file in sorted(image_files):
        print(f"\n  Processing {image_file.name}...", end=" ", flush=True)
        start = time.time()
        ocr_text = run_ocr(str(image_file))
        elapsed = time.time() - start
        print(f"✓ {elapsed:.2f}s, {len(ocr_text)} chars")
        image_ocr_pairs.append((image_file.name, ocr_text))

    # Run LLM benchmarks
    results = await run_benchmarks(image_ocr_pairs)
    print_summary(results)

    # Save results
    output_dir = Path(__file__).parent.parent / "benchmark_results" / "llm_providers"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Save JSON results
    json_file = output_dir / f"results_{timestamp}.json"
    results_dict = [
        {
            "provider": r.provider,
            "model": r.model,
            "image_name": r.image_name,
            "success": r.success,
            "latency_seconds": r.latency_seconds,
            "time_to_first_token": r.time_to_first_token,
            "tokens_per_second": r.tokens_per_second,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "total_tokens": r.total_tokens,
            "cost_usd": r.cost_usd,
            "ingredient_count": r.ingredient_count,
            "instruction_count": r.instruction_count,
            "recipe_data": r.recipe_data,
            "error": r.error
        }
        for r in results
    ]

    with open(json_file, "w") as f:
        json.dump({"generated_at": timestamp, "results": results_dict}, f, indent=2, ensure_ascii=False)

    print(f"\nJSON results saved to: {json_file}")

    # Generate and save markdown report with full recipes
    md_file = output_dir / f"recipe_comparison_{timestamp}.md"
    md_report = generate_recipe_report(results, output_dir)
    with open(md_file, "w") as f:
        f.write(md_report)

    print(f"Recipe comparison saved to: {md_file}")
    print("\nOpen the markdown file to compare recipe quality across models!")


if __name__ == "__main__":
    asyncio.run(main())
