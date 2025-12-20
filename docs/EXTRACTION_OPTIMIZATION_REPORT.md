# Recipe Extraction Optimization Report

**Date**: December 15, 2025
**Goal**: Reduce extraction time to under 10 seconds while maintaining quality and keeping costs under $0.05 per extraction

---

## Executive Summary

After comprehensive benchmarking of LLM providers, OCR configurations, and extraction strategies, we identified optimizations that can reduce photo extraction time from **~25 seconds to ~8-9 seconds** (3x faster) while maintaining quality and reducing costs.

### Key Findings

| Area | Current | Recommended | Improvement |
|------|---------|-------------|-------------|
| LLM Provider | GPT-4o-mini (~22s) | Gemini 2.5 Flash Lite (~5s) | **4.5x faster** |
| LLM Cost | $0.0007/extraction | $0.0005/extraction | 30% cheaper |
| OCR Config | Default Tesseract | Enhanced preprocessing + PSM 3 | Better accuracy |
| Photo Strategy | OCR + Vision | OCR-only (text extraction) | Simpler, faster |

---

## Part 1: LLM Provider Benchmarking

### Test Setup
- **6 real recipe images** from `benchmark_inputs/`
- **Production prompt** from `openai_service.py`
- **Metrics**: Latency, TTFT, cost, ingredient count, instruction count

### Results (Averaged Across 6 Images)

| Model | Avg Latency | Avg Cost | Avg Ingredients | Reliability |
|-------|-------------|----------|-----------------|-------------|
| **gemini-2.5-flash-lite** | **4.85s** | **$0.0005** | 12.8 | 100% (6/6) |
| gemini-2.0-flash | 7.57s | $0.0006 | 13.0 | 100% (6/6) |
| gemini-2.0-flash-lite | 8.57s | $0.0005 | 13.0 | 100% (6/6) |
| claude-3-5-haiku-latest | 15.02s | $0.0059 | 10.0 | 17% (1/6) |
| gpt-4o | 15.69s | $0.0114 | 12.3 | 100% (6/6) |
| **gpt-4o-mini (current)** | **21.62s** | **$0.0007** | 11.8 | 100% (6/6) |
| gemini-2.5-flash | 28.23s | $0.0012 | 13.5 | 33% (2/6) |

### Detailed Per-Image Results

| Image | gemini-2.5-flash-lite | gpt-4o-mini | Speedup |
|-------|----------------------|-------------|---------|
| IMG_5357.HEIC | 4.92s | 18.91s | 3.8x |
| IMG_5362.HEIC | 2.28s | 18.64s | 8.2x |
| IMG_5363.HEIC | 8.26s | 26.69s | 3.2x |
| IMG_5365.HEIC | 2.84s | 15.98s | 5.6x |
| IMG_5482.HEIC | 4.07s | 22.70s | 5.6x |
| IMG_5485.HEIC | 6.75s | 26.79s | 4.0x |

### Quality Comparison

All models extracted similar quality recipes. Example from IMG_5357.HEIC (Carrot Soup):

**gemini-2.5-flash-lite** (4.92s):
- Title: "Velouté de carottes au cumin"
- 10 ingredients with proper grouping ("For the soup", "For the garnish", "To taste")
- 5 instruction steps with timers
- Correctly identified: 12 carrots, 6 scallops, 50g butter

**gpt-4o-mini** (18.91s):
- Title: "Velouté de Carottes au Cumin et Saint-Jacques"
- 10 ingredients (less organized grouping)
- 5 instruction steps with timers
- Same ingredient extraction accuracy

### Provider Issues Discovered

1. **gemini-2.5-flash**: Unstable, frequent failures (500 errors, empty responses)
2. **claude-3-5-haiku**: JSON parsing issues - returns non-JSON responses 5/6 times
3. **gemini-2.5-flash-lite**: Most stable Gemini model, 100% success rate

### Recommendation

**Switch from `gpt-4o-mini` to `gemini-2.5-flash-lite`**

Benefits:
- 4.5x faster (4.85s vs 21.62s average)
- 30% cheaper ($0.0005 vs $0.0007)
- Better ingredient extraction (12.8 vs 11.8 average)
- 100% reliability in testing
- Proper ingredient grouping

---

## Part 2: OCR Configuration Optimization

### Problem
Initial OCR was misreading quantities (e.g., "12 carrots" → "6 carrots")

### Solution
Enhanced Tesseract preprocessing with:

```python
# 1. Upscale small images to minimum 2000px
min_dimension = 2000
if min(image.size) < min_dimension:
    ratio = min_dimension / min(image.size)
    new_size = tuple(int(dim * ratio) for dim in image.size)
    image = image.resize(new_size, Image.Resampling.LANCZOS)

# 2. Strong contrast enhancement (2.0)
enhancer = ImageEnhance.Contrast(image)
image = enhancer.enhance(2.0)

# 3. Strong sharpening (2.0)
enhancer = ImageEnhance.Sharpness(image)
image = enhancer.enhance(2.0)

# 4. Slight brightness increase (1.1)
enhancer = ImageEnhance.Brightness(image)
image = enhancer.enhance(1.1)

# 5. Use PSM 3 for mixed layouts
custom_config = r'--oem 3 --psm 3'
```

### Results

| Configuration | "12 CAROTTES" Detection | Overall Accuracy |
|---------------|------------------------|------------------|
| Default Tesseract | ❌ "6 CAROTTES" | Poor |
| Enhanced (PSM 6) | ❌ "6 CAROTTES" | Moderate |
| **Enhanced (PSM 3)** | ✅ "12 CAROTTES" | **Good** |

### OCR Timing
- Average OCR time: **3-4 seconds** per image
- Consistent across all 6 test images

---

## Part 3: Photo Extraction Strategies

### Strategies Tested

| Strategy | Description | Steps |
|----------|-------------|-------|
| `full` | Current production | OCR → GPT-4o-mini Vision (image + OCR) |
| `ocr_only` | Text extraction only | OCR → LLM (text only, no image) |
| `vision_only` | Skip OCR | GPT-4o-mini Vision (image only) |

### Results (from benchmark_extraction_direct.py)

| Strategy | Time | Cost | Ingredients | Steps |
|----------|------|------|-------------|-------|
| ocr_only | ~8s | $0.0005 | 10+ | 5+ |
| full | ~25s | $0.003 | 10+ | 5+ |
| vision_only | ~20s | $0.003 | 10+ | 5+ |

### Key Insight

For **recipe cards with visible text**, the `ocr_only` strategy:
- Is 3x faster (no image encoding/transmission)
- Is 6x cheaper (text tokens vs image tokens)
- Produces equivalent quality

The Vision model adds value only for:
- Food photos (no text visible)
- Verifying/correcting OCR errors
- Images with complex layouts

### Recommendation

Use **hybrid approach**:
1. Always run OCR first (~3-4s)
2. If OCR extracts substantial text (>200 chars), use `ocr_only` with Gemini
3. If OCR fails or returns minimal text, fall back to Vision model

---

## Part 4: Video Extraction Strategies

### Strategies Available

| Strategy | Description | Components |
|----------|-------------|------------|
| `full` | Complete extraction | Download → Audio → Frames → Transcribe → OCR → Normalize → Image Gen |
| `no_ocr` | Skip frame OCR | Download → Audio → Transcribe → Normalize → Image Gen |
| `transcript_only` | Audio only | Download → Audio → Transcribe → Normalize |
| `description_only` | Metadata only | Download (metadata) → Normalize |
| `no_image_gen` | Skip Flux | All steps except image generation |

### Timing Breakdown (Typical Video)

| Step | Time | Notes |
|------|------|-------|
| Download | 5-10s | Depends on video length/source |
| Audio extraction | 2-3s | FFmpeg |
| Frame extraction | 1-2s | Every 5 seconds |
| Transcription | 10-15s | Whisper API |
| Frame OCR | 5-10s | Multiple frames |
| Normalization | 15-25s | GPT-4o-mini |
| Image generation | 10-15s | Flux ($0.04/image) |
| **Total** | **50-80s** | |

### Recommendations

1. **For TikTok/Instagram**: Use `full` strategy (recipes often in text overlays)
2. **For YouTube**: Consider `transcript_only` (better audio, less text overlays)
3. **Skip image gen** for faster extraction when thumbnail exists

---

## Part 5: Cost Analysis

### Current Costs (per extraction)

| Component | Photo | Video |
|-----------|-------|-------|
| OCR (Tesseract) | Free | Free |
| Whisper Transcription | - | ~$0.006 |
| LLM Normalization (GPT-4o-mini) | $0.0007 | $0.001-0.002 |
| Vision (if used) | $0.003 | - |
| Flux Image Gen | - | $0.04 |
| **Total** | **$0.001-0.004** | **$0.05-0.07** |

### Optimized Costs

| Component | Photo | Video |
|-----------|-------|-------|
| OCR (Tesseract) | Free | Free |
| Whisper Transcription | - | ~$0.006 |
| LLM Normalization (Gemini) | **$0.0005** | **$0.0008** |
| Vision (if used) | $0.003 | - |
| Flux Image Gen | - | $0.04 |
| **Total** | **$0.0005-0.003** | **$0.047-0.05** |

---

## Implementation Plan

### Phase 1: LLM Provider Switch (High Impact, Low Effort)

**Files to modify:**
- `app/services/llm_service.py` - Already created with multi-provider support
- `app/services/openai_service.py` - Update to use LLMService

**Changes:**
```python
# In openai_service.py or create new extraction service
from app.services.llm_service import LLMService

class RecipeExtractionService:
    def __init__(self):
        # Use Gemini as primary, OpenAI as fallback
        self.llm = LLMService(preferred_provider="gemini")

    async def extract_from_ocr(self, ocr_text: str) -> dict:
        return await self.llm.generate(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=get_user_prompt(ocr_text)
        )
```

**Expected improvement:**
- Photo extraction: 25s → 8-9s (3x faster)

### Phase 2: OCR Optimization (Already Done)

**Files modified:**
- `app/services/extractors/photo_extractor.py`

**Changes implemented:**
- Image upscaling to minimum 2000px
- Contrast enhancement (2.0)
- Sharpening (2.0)
- Brightness adjustment (1.1)
- PSM 3 configuration

**Status:** ✅ Complete

### Phase 3: Hybrid Strategy (Medium Impact, Medium Effort)

**Concept:**
```python
async def extract_recipe_smart(self, image_source: str) -> dict:
    # Step 1: Run OCR
    ocr_text = await self._run_ocr(image_source)

    # Step 2: Decide strategy based on OCR quality
    if len(ocr_text) > 200 and self._looks_like_recipe(ocr_text):
        # OCR-only: faster, cheaper
        return await self.llm.generate(
            system_prompt=OCR_ONLY_PROMPT,
            user_prompt=ocr_text
        )
    else:
        # Fall back to Vision for food photos or poor OCR
        return await self._extract_with_vision(image_source, ocr_text)
```

### Phase 4: Environment Configuration

Add to `.env`:
```env
# LLM Provider Configuration
GOOGLE_API_KEY=your_google_api_key
PREFERRED_LLM_PROVIDER=gemini  # gemini, openai, or anthropic
FALLBACK_LLM_PROVIDER=openai

# Extraction Settings
PHOTO_EXTRACTION_STRATEGY=hybrid  # ocr_only, vision, hybrid
VIDEO_EXTRACTION_STRATEGY=full    # full, no_ocr, transcript_only
```

---

## Files Reference

### Benchmark Scripts
- `scripts/benchmark_llm_providers.py` - LLM provider comparison
- `scripts/benchmark_extraction_direct.py` - Extraction strategy comparison
- `scripts/compare_ocr_engines.py` - OCR engine comparison

### Results
- `benchmark_results/llm_providers/recipe_comparison_2025-12-15_15-35-01.md` - Full LLM comparison
- `benchmark_results/llm_providers/results_2025-12-15_15-35-01.json` - Raw benchmark data

### Production Code
- `app/services/llm_service.py` - Multi-provider LLM service (new)
- `app/services/openai_service.py` - Current extraction service
- `app/services/extractors/photo_extractor.py` - Photo extraction with OCR

---

## Conclusion

By switching from GPT-4o-mini to Gemini 2.5 Flash Lite and using our optimized OCR configuration, we can achieve:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Photo extraction time | ~25s | ~8-9s | **3x faster** |
| LLM latency | ~22s | ~5s | **4.5x faster** |
| Cost per extraction | $0.003 | $0.001 | **3x cheaper** |
| Ingredient accuracy | Good | Good | Same |
| Reliability | 100% | 100% | Same |

**Next Steps:**
1. Update `openai_service.py` to use `LLMService` with Gemini as default
2. Add environment variable for provider selection
3. Implement hybrid strategy for smart OCR/Vision selection
4. Monitor production metrics after deployment
