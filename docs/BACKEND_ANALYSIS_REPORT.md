# Cuisto Backend Analysis & Refactoring Report

## Executive Summary

This document provides an extensive analysis of the cuisto-server backend codebase covering:
1. **Architecture & Structure Assessment** - Is the current structure still appropriate for the codebase size?
2. **Extraction Process Deep Dive** - Complete analysis with strengths, limitations, and rewrite recommendations
3. **Code Quality Audit** - Best practices, readability, performance considerations
4. **Actionable Refactoring Recommendations** - Prioritized changes with effort estimates

---

## Table of Contents

1. [Codebase Overview](#1-codebase-overview)
2. [Architecture Assessment](#2-architecture-assessment)
3. [Extraction Process Analysis](#3-extraction-process-analysis)
4. [Code Quality Analysis](#4-code-quality-analysis)
5. [Performance & Cost Analysis](#5-performance--cost-analysis)
6. [Refactoring Recommendations](#6-refactoring-recommendations)
7. [Ideal Rewrite Architecture](#7-ideal-rewrite-architecture)

---

## 1. Codebase Overview

### 1.1 Current Statistics

| Metric | Count |
|--------|-------|
| Python files | ~80 |
| Services | 17 |
| Repositories | 15 |
| API Endpoints | 15 modules |
| Database tables | 31+ |
| Lines of code (estimate) | ~15,000-20,000 |

### 1.2 Directory Structure

```
cuisto-server/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/      # 15 endpoint modules (~300KB total)
│   │   └── schemas/        # 13 schema modules
│   ├── core/               # 8 infrastructure modules
│   ├── domain/             # 4 domain modules
│   ├── repositories/       # 15 repository modules
│   └── services/           # 17 service modules
│       └── extractors/     # 5 extractor modules
├── database/migrations/    # 31 migrations
├── main.py
└── requirements.txt
```

### 1.3 Architectural Pattern

The codebase implements **Clean Architecture** with these layers:
- **API Layer** (`api/v1/`) - HTTP interface, request/response handling
- **Service Layer** (`services/`) - Business logic orchestration
- **Repository Layer** (`repositories/`) - Data access abstraction
- **Domain Layer** (`domain/`) - Business entities, enums, exceptions

---

## 2. Architecture Assessment

### 2.1 Is the Structure Still Appropriate?

**Verdict: YES, with minor adjustments needed**

The Clean Architecture pattern you've chosen is **excellent** for a codebase of this size and complexity. It provides:
- Clear separation of concerns
- Testability (though tests are missing)
- Flexibility for future growth
- Maintainable code organization

However, some structural issues have emerged as the codebase grew:

### 2.2 Structural Issues Identified

#### Issue 1: Monolithic Services (Severity: Medium)

**Problem:** Some services have grown too large and handle multiple responsibilities:
- `extraction_service.py` - 1,261 lines, handles extraction orchestration + job management + duplicate detection
- `moderation_service.py` - 55KB, combines moderation logic, user actions, and admin operations

**Recommendation:** Split into focused services:
```
services/
├── extraction/
│   ├── extraction_orchestrator.py  # Main flow coordination
│   ├── job_service.py               # Job CRUD & status management
│   └── duplicate_service.py         # Duplicate detection logic
├── moderation/
│   ├── report_handler.py
│   ├── user_moderation.py
│   └── admin_actions.py
```

#### Issue 2: Heavy Service Coupling (Severity: High)

**Problem:** `ExtractionService.__init__` creates 10+ dependencies directly:
```python
def __init__(self, supabase: Client):
    self.gemini_service = GeminiService()
    self.flux_service = FluxService(supabase)
    self.recipe_repo = RecipeRepository(supabase)
    self.video_source_repo = VideoSourceRepository(supabase)
    self.category_repo = CategoryRepository(supabase)
    self.recipe_save_service = RecipeSaveService(supabase)
    self.thumbnail_cache = ThumbnailCacheService(supabase)
    self.credit_service = CreditService(supabase)
    self.subscription_service = SubscriptionService(supabase)
```

**Impact:**
- Difficult to test in isolation (need to mock 10+ classes)
- Hidden dependencies (caller doesn't know what's used)
- Changes to one service may break others

**Recommendation:** Use dependency injection container:
```python
# Option 1: Constructor injection
class ExtractionService:
    def __init__(
        self,
        gemini: GeminiService,
        flux: FluxService,
        recipe_repo: RecipeRepository,
        # ... explicit dependencies
    ):
        pass

# Option 2: Use a DI container (e.g., dependency-injector, punq)
```

#### Issue 3: Missing Service Interfaces (Severity: Low-Medium)

**Problem:** No abstract base classes for services, making it harder to:
- Swap implementations (e.g., mock AI service for testing)
- Document expected interfaces
- Enforce contracts

**Recommendation:** Create protocol classes for key services:
```python
class AIServiceProtocol(Protocol):
    async def normalize_recipe(self, content: str, source_type: str) -> dict: ...

class ImageGeneratorProtocol(Protocol):
    async def generate_recipe_image(self, recipe_data: dict, user_id: str) -> str: ...
```

#### Issue 4: Endpoint File Size (Severity: Low)

**Problem:** Some endpoint files are very large:
- `auth.py` - 64KB
- `recipes.py` - 49KB
- `admin.py` - 27KB

**Recommendation:** Split by feature subset:
```
endpoints/
├── auth/
│   ├── login.py
│   ├── registration.py
│   └── profile.py
├── recipes/
│   ├── crud.py
│   ├── search.py
│   └── sharing.py
```

### 2.3 What's Working Well

1. **Clear layer separation** - API never directly accesses database
2. **Repository abstraction** - BaseRepository provides consistent CRUD
3. **Domain isolation** - Enums, models, exceptions are framework-agnostic
4. **Consistent patterns** - Similar code structure across files
5. **Type hints everywhere** - Helps with IDE support and documentation

---

## 3. Extraction Process Analysis

### 3.1 Complete Extraction Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT REQUEST                              │
│  POST /api/v1/extraction/submit                                  │
│  { source_type: "video", source_url: "tiktok.com/..." }         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: AUTHENTICATION & VALIDATION                             │
│  ├─ Verify JWT token                                             │
│  ├─ Check subscription status (premium vs free)                  │
│  └─ Check credit balance (free users: 5 credits/week)           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: DUPLICATE DETECTION                                     │
│  ├─ For videos: Check video_sources by platform + video_id      │
│  ├─ For URLs: Check recipes by normalized source_url            │
│  └─ If duplicate found: Mark as extracted, return existing      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: JOB CREATION (0% progress)                              │
│  ├─ Create extraction_jobs record (status: PENDING)              │
│  └─ Return job_id immediately to client                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: BACKGROUND EXTRACTION (0-70% progress)                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ VideoExtractor                                            │   │
│  │ ├─ Download video (yt-dlp)              [5-30%]          │   │
│  │ ├─ Extract audio (MoviePy)              [30-50%]         │   │
│  │ ├─ Transcribe (Whisper local)           [50-90%]         │   │
│  │ └─ Combine transcript + description     [90-100%]        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ PhotoExtractor                                            │   │
│  │ ├─ Download images                      [5-20%]          │   │
│  │ ├─ Preprocess (resize, enhance)         [20-40%]         │   │
│  │ ├─ OCR with Tesseract                   [40-70%]         │   │
│  │ └─ Send to Gemini for structuring       [70-100%]        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ LinkExtractor                                             │   │
│  │ ├─ Detect URL type (video vs webpage)   [5-10%]          │   │
│  │ ├─ If video: Delegate to VideoExtractor                  │   │
│  │ ├─ If webpage: Fetch HTML               [10-30%]         │   │
│  │ ├─ Parse schema.org/microdata           [30-50%]         │   │
│  │ ├─ Extract text content                 [50-70%]         │   │
│  │ └─ Extract og:image/twitter:image       [70-100%]        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ VoiceExtractor                                            │   │
│  │ ├─ Validate audio format                [5-20%]          │   │
│  │ └─ Transcribe with Whisper              [20-100%]        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ PasteExtractor                                            │   │
│  │ └─ Clean and validate text              [0-100%]         │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: SPECIAL CASE - CLIENT-SIDE DOWNLOAD                     │
│  (Instagram and other blocked platforms)                         │
│                                                                  │
│  ├─ Extract direct MP4 URL using yt-dlp (no download)           │
│  ├─ Update job status to NEEDS_CLIENT_DOWNLOAD                  │
│  ├─ Return video_download_url to client                         │
│  ├─ Client downloads video using their IP                       │
│  ├─ Client uploads video to /upload/video                       │
│  └─ Server resumes extraction with uploaded file                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: AI NORMALIZATION (70% progress)                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ GeminiService.normalize_recipe()                          │   │
│  │ ├─ Build system prompt with category options              │   │
│  │ ├─ Send raw text to Gemini 2.5 Flash Lite                │   │
│  │ ├─ Parse JSON response                                    │   │
│  │ ├─ Validate is_recipe flag                                │   │
│  │ ├─ If NotARecipe: Return early with NOT_A_RECIPE status  │   │
│  │ └─ If Gemini refuses (copyright): Fallback to GPT-4o-mini│   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Output:                                                         │
│  {                                                               │
│    title, description, language,                                 │
│    ingredients: [{name, quantity, unit, notes, group}],         │
│    instructions: [{step_number, title, description, timer_minutes, group}],│
│    servings, difficulty, category_slug, tags[],                 │
│    prep_time_minutes, cook_time_minutes, resting_time_minutes   │
│  }                                                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: IMAGE HANDLING (80-90% progress)                        │
│                                                                  │
│  ├─ Video sources: Use thumbnail from yt-dlp metadata           │
│  ├─ Link/URL sources: Use og:image or schema.org image          │
│  └─ Photo/Voice/Paste: Generate AI image with Flux              │
│                                                                  │
│  Flux Image Generation:                                          │
│  ├─ Build prompt from recipe title + description                │
│  ├─ Call Flux AI API                                            │
│  ├─ Upload generated image to Supabase Storage                  │
│  └─ Return public URL                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 8: RECIPE SAVE (90% progress)                              │
│                                                                  │
│  RecipeSaveService.create_draft_recipe():                        │
│  ├─ Resolve category_slug → category_id                         │
│  ├─ Calculate total_time_minutes                                │
│  ├─ INSERT INTO recipes (is_draft=true)                         │
│  ├─ INSERT INTO recipe_contributors                              │
│  ├─ INSERT INTO user_recipe_data (was_extracted=true)           │
│  └─ If video: INSERT INTO video_sources + video_creators        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 9: CREDIT DEDUCTION & COMPLETION (100% progress)           │
│                                                                  │
│  ├─ Check if user is premium (skip credit deduction)            │
│  ├─ Deduct 1 credit from user balance                           │
│  ├─ Update extraction_jobs status to COMPLETED                  │
│  ├─ Broadcast completion event via SSE                          │
│  └─ Return recipe_id to client                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST-EXTRACTION: USER CONFIRMATION                              │
│                                                                  │
│  User reviews draft recipe in app:                               │
│  ├─ Can edit title, ingredients, instructions                   │
│  ├─ Can change category                                          │
│  └─ Calls POST /recipes/save to publish (is_draft=false)        │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Extraction Process Strengths

| Strength | Description | Impact |
|----------|-------------|--------|
| **Multi-source Support** | 5 extractors for video, photo, voice, link, paste | High flexibility for users |
| **Smart Duplicate Detection** | Checks video platform+id and normalized URLs | Saves API costs, better UX |
| **Cost Optimization** | Gemini 2.5 Flash Lite (4x cheaper than GPT-4) | ~$0.0003 per extraction |
| **OCR-only Photo Extraction** | Tesseract OCR instead of Vision API | 98% cheaper than GPT-4 Vision |
| **Fallback Mechanism** | Gemini → GPT-4o-mini for copyright blocks | Better reliability |
| **Real-time Progress** | SSE broadcasting with granular progress | Great UX |
| **Client-side Download** | Bypass Instagram IP blocking | Works where others fail |
| **Two-phase Save** | Draft → Preview → Publish | User control |
| **Async-first Design** | `asyncio.to_thread()` for blocking ops | Non-blocking, scalable |
| **Temp File Cleanup** | Automatic cleanup in finally blocks | No disk leaks |

### 3.3 Extraction Process Limitations

#### Limitation 1: No Retry Logic (Severity: High)

**Problem:** API calls to Gemini/OpenAI/Flux fail immediately without retry.

**Code Location:** `gemini_service.py:477`, `extraction_service.py:171`

**Impact:**
- Transient network errors cause extraction failure
- User must manually retry
- Wasted CPU time (video already downloaded/transcribed)

**Recommendation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def normalize_recipe(self, raw_content: str, source_type: str):
    # ... existing code
```

#### Limitation 2: No Circuit Breaker (Severity: Medium)

**Problem:** If Gemini API is down, all extractions fail continuously, wasting resources.

**Impact:**
- Video download + transcription completes, then fails at normalization
- User frustration, server load

**Recommendation:** Use `pybreaker` or custom implementation:
```python
from pybreaker import CircuitBreaker

gemini_breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

@gemini_breaker
async def normalize_recipe(self, ...):
    pass
```

#### Limitation 3: Progress Callback Code Duplication (Severity: Medium)

**Problem:** Progress callback logic is duplicated in `extract_recipe()` and `extract_and_create_recipe()`:
```python
# Same ~50 lines appear in both methods
def sync_progress_callback(percentage: int, step: str):
    scaled_percentage = int(percentage * 0.7)
    if progress_callback:
        progress_callback(scaled_percentage, step)
    if job_id:
        asyncio.create_task(self._update_job_status(...))
```

**Recommendation:** Extract to helper method or decorator.

#### Limitation 4: Fire-and-Forget Background Tasks (Severity: Medium)

**Problem:** `asyncio.create_task()` used for progress updates without error handling:
```python
asyncio.create_task(self._update_job_status(...))  # Errors silently ignored
```

**Impact:**
- Progress updates may silently fail
- Thumbnail refresh failures not noticed
- Debugging difficult

**Recommendation:**
```python
async def _safe_task(coro, name: str):
    try:
        return await coro
    except Exception as e:
        logger.error(f"Background task '{name}' failed: {e}")

asyncio.create_task(_safe_task(
    self._update_job_status(...),
    "progress_update"
))
```

#### Limitation 5: No Request Timeouts (Severity: Medium)

**Problem:** External API calls don't have explicit timeouts.

**Code Location:** `gemini_service.py:474-477`

**Impact:**
- Slow API responses block extraction indefinitely
- Job appears stuck

**Recommendation:**
```python
import asyncio

async def normalize_recipe(self, ...):
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(_generate),
            timeout=60.0  # 60 second timeout
        )
    except asyncio.TimeoutError:
        raise ExtractionTimeoutError("AI normalization timed out")
```

#### Limitation 6: Hardcoded Model Selection (Severity: Low)

**Problem:** AI models are hardcoded:
```python
MODEL_NAME = "gemini-2.5-flash-lite"  # Hardcoded
OPENAI_MODEL = "gpt-4o-mini"  # Hardcoded
```

**Impact:**
- Can't A/B test different models
- Requires code change to switch models
- Can't use different models for different source types

**Recommendation:** Move to configuration:
```python
class Settings(BaseSettings):
    AI_MODEL_NORMALIZATION: str = "gemini-2.5-flash-lite"
    AI_MODEL_FALLBACK: str = "gpt-4o-mini"
    AI_MODEL_OCR: str = "gemini-2.5-flash-lite"
```

#### Limitation 7: No Extraction Metrics (Severity: Low)

**Problem:** No structured metrics for:
- Extraction success rate by source type
- Average extraction time
- AI model cost tracking
- Error categorization

**Impact:**
- Can't optimize based on data
- Hard to identify issues
- No cost tracking

**Recommendation:** Add structured logging/metrics:
```python
logger.info("extraction_complete", extra={
    "source_type": source_type,
    "duration_seconds": duration,
    "ai_model": model_used,
    "tokens_used": token_count,
    "cost_usd": cost,
    "success": True
})
```

#### Limitation 8: Memory Pressure with Large Videos (Severity: Medium)

**Problem:** Large videos fully loaded into memory during processing.

**Code Location:** `video_extractor.py:248-252`
```python
video = VideoFileClip(video_path)  # Full video in memory
video.audio.write_audiofile(audio_path, logger=None)
```

**Impact:**
- Large videos can cause OOM on constrained servers
- Multiple concurrent extractions compound the issue

**Recommendation:**
- Add file size limits (already have `MAX_UPLOAD_SIZE_MB`)
- Use streaming audio extraction
- Consider FFmpeg direct command instead of MoviePy

### 3.4 Extraction Cost Analysis

| Component | Cost per Extraction | Notes |
|-----------|---------------------|-------|
| Gemini 2.5 Flash Lite | ~$0.0003 | ~1K input, ~500 output tokens |
| GPT-4o-mini (fallback) | ~$0.0006 | Only when Gemini refuses |
| Flux Image Generation | ~$0.01-0.05 | Only for voice/paste sources |
| Whisper (local) | $0 | CPU cost only |
| Tesseract OCR | $0 | CPU cost only |
| **Total (Video)** | **~$0.0003** | Most common case |
| **Total (Photo)** | **~$0.0003** | OCR + Gemini |
| **Total (with image gen)** | **~$0.02** | Voice/paste sources |

**Cost Optimization Wins:**
- OCR instead of Vision API: **98% cheaper** ($0.0003 vs $0.01+)
- Gemini vs GPT-4: **4x cheaper** on input, 2x cheaper on output
- Local Whisper vs API: **Free** vs $0.006/minute

---

## 4. Code Quality Analysis

### 4.1 Positive Patterns

#### Pattern 1: Consistent Type Hints
```python
async def extract_recipe(
    self,
    user_id: str,
    source_type: SourceType,
    source: Union[str, List[str]],
    job_id: Optional[str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Dict[str, Any]:
```
**Verdict:** Excellent type coverage throughout.

#### Pattern 2: Domain Enums
```python
class SourceType(str, Enum):
    VIDEO = "video"
    PHOTO = "photo"
    VOICE = "voice"
    PASTE = "paste"
    LINK = "link"
```
**Verdict:** Good use of enums for type safety.

#### Pattern 3: Custom Exceptions
```python
class NotARecipeError(Exception):
    def __init__(self, message: str = "Content is not a recipe"):
        self.message = message
        super().__init__(self.message)
```
**Verdict:** Clear exception hierarchy.

#### Pattern 4: Async-First Design
```python
# CPU-intensive operations wrapped properly
await asyncio.to_thread(_sync_download)
await asyncio.to_thread(_sync_transcribe)
```
**Verdict:** Non-blocking design throughout.

### 4.2 Issues Found

#### Issue 1: Debug Logging in Production Code

**Location:** `repositories/base.py:40-44`
```python
logger.info(f"[BASE REPO] Updating {self.table_name} id={record_id} with data keys: {list(data.keys())}")
if "category_id" in data:
    logger.info(f"[BASE REPO] category_id value being sent: {data['category_id']}")
```

**Problem:** Debug statements left in production code.

**Recommendation:** Remove or move to DEBUG level:
```python
logger.debug(f"Updating {self.table_name} id={record_id}")
```

#### Issue 2: Broad Exception Handling

**Location:** Multiple files
```python
except Exception as e:
    logger.error(f"Error: {str(e)}")
    raise
```

**Problem:** Catches all exceptions without specific handling.

**Recommendation:** Catch specific exceptions:
```python
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error: {e.response.status_code}")
    raise ExtractionAPIError(f"API returned {e.response.status_code}")
except httpx.TimeoutException:
    logger.error("Request timed out")
    raise ExtractionTimeoutError()
```

#### Issue 3: Async Methods That Aren't Async

**Location:** `repositories/base.py:19-26`
```python
async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        response = self.supabase.table(self.table_name).insert(data).execute()
        # ^ This is a synchronous call!
```

**Problem:** Methods marked `async` but make synchronous Supabase calls.

**Impact:**
- Blocks event loop during database operations
- False expectation of non-blocking behavior

**Recommendation:** Wrap in `asyncio.to_thread()`:
```python
async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    response = await asyncio.to_thread(
        lambda: self.supabase.table(self.table_name).insert(data).execute()
    )
```

#### Issue 4: Missing Input Validation

**Location:** `extraction_service.py:50-70`

**Problem:** Source URL not validated before processing.

**Recommendation:**
```python
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc
```

#### Issue 5: Dict Unpacking Without Validation

**Location:** Multiple files
```python
recipe_id = result["recipe_id"]  # May raise KeyError
```

**Recommendation:**
```python
recipe_id = result.get("recipe_id")
if not recipe_id:
    raise ExtractionError("Recipe creation failed - no recipe_id returned")
```

#### Issue 6: No Transaction Support

**Location:** `recipe_save_service.py`, `extraction_service.py`

**Problem:** Multi-table operations aren't atomic:
```python
# These operations can partially fail
recipe = await self.recipe_repo.create(recipe_data)
self.supabase.table("recipe_contributors").insert({...}).execute()
# If second fails, orphan recipe exists
```

**Supabase Limitation:** REST API doesn't support transactions.

**Recommendation:** Use Supabase Edge Functions with `supabase-js` for transactions, or implement compensating transactions:
```python
try:
    recipe = await self.recipe_repo.create(recipe_data)
    try:
        await create_contributor(recipe["id"])
    except Exception:
        await self.recipe_repo.delete(recipe["id"])  # Rollback
        raise
except Exception:
    raise
```

### 4.3 Testing Gap (Critical)

**Current State:** Only 1 test file found (`test_phone_auth.py`)

**Missing Test Coverage:**
- Unit tests for services (CreditService logic is complex)
- Repository tests
- API endpoint tests
- Extraction pipeline integration tests

**Priority Testing Areas:**
1. `CreditService` - Complex weekly reset logic
2. `ExtractionService.extract_recipe()` - Main flow
3. `GeminiService.normalize_recipe()` - AI parsing
4. `RecipeRepository` rating aggregation

---

## 5. Performance & Cost Analysis

### 5.1 Current Performance Characteristics

| Operation | Typical Duration | Bottleneck |
|-----------|------------------|------------|
| Video download | 5-30s | Network, platform rate limits |
| Audio extraction | 2-5s | CPU (MoviePy) |
| Whisper transcription | 10-60s | CPU (local model) |
| Gemini normalization | 1-3s | Network |
| Flux image generation | 5-15s | Network, API |
| Database operations | 50-200ms | Network |
| **Total (video)** | **20-100s** | Whisper transcription |
| **Total (photo)** | **5-20s** | OCR + Gemini |
| **Total (link)** | **3-15s** | Page fetch + Gemini |

### 5.2 Performance Optimization Opportunities

#### Opportunity 1: Parallel Operations

**Current:** Sequential extraction steps
**Improvement:** Parallelize independent operations:
```python
# Current: Sequential
video_path = await self._download_video(source)
audio_path = await self._extract_audio(video_path)

# Improved: Parallel where possible
download_task = asyncio.create_task(self._download_video(source))
# Start metadata extraction while downloading
metadata = await self._extract_metadata_only(source)
video_path = await download_task
```

#### Opportunity 2: Whisper Model Selection

**Current:** Uses "base" model by default
**Improvement:** Use "tiny" for short videos, "base" for longer:
```python
def get_whisper_model(duration_seconds: int):
    if duration_seconds < 60:
        return whisper.load_model("tiny")  # Faster for shorts
    return whisper.load_model("base")
```

#### Opportunity 3: Connection Pooling

**Current:** New Supabase client per request
**Improvement:** Use connection pooling (if supported by SDK)

### 5.3 Resource Utilization

| Resource | Current Usage | Recommendation |
|----------|---------------|----------------|
| CPU | High (Whisper) | Consider GPU instance or Whisper API |
| Memory | Medium (MoviePy loads full video) | Stream processing |
| Disk | Temp files cleaned up | Good |
| Network | Sequential requests | Batch where possible |

---

## 6. Refactoring Recommendations

### 6.1 Priority 1: Critical (Do First)

#### R1.1: Add Retry Logic to External APIs

**Files:** `gemini_service.py`, `flux_service.py`, `openai_service.py`

**Change:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, TimeoutError))
)
async def normalize_recipe(self, ...):
    pass
```

**Effort:** ~2 hours
**Impact:** High - prevents transient failures

#### R1.2: Add Request Timeouts

**Files:** `gemini_service.py`, all API services

**Change:**
```python
response = await asyncio.wait_for(
    asyncio.to_thread(_generate),
    timeout=60.0
)
```

**Effort:** ~1 hour
**Impact:** High - prevents hung jobs

#### R1.3: Fix Async Repository Methods

**File:** `repositories/base.py`

**Change:** Wrap all Supabase calls in `asyncio.to_thread()`:
```python
async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    def _sync_create():
        return self.supabase.table(self.table_name).insert(data).execute()

    response = await asyncio.to_thread(_sync_create)
    return response.data[0] if response.data else None
```

**Effort:** ~2 hours
**Impact:** High - prevents event loop blocking

### 6.2 Priority 2: High (Do Soon)

#### R2.1: Implement Dependency Injection

**Files:** `extraction_service.py`, `app.py`

**Change:** Use constructor injection or DI container:
```python
# Option A: Manual DI
class ExtractionService:
    def __init__(
        self,
        supabase: Client,
        gemini: GeminiService,
        flux: FluxService,
        recipe_repo: RecipeRepository,
        # ...
    ):
        self.gemini = gemini
        # ...

# In endpoint/factory:
gemini = GeminiService()
flux = FluxService(supabase)
extraction = ExtractionService(supabase, gemini, flux, ...)
```

**Effort:** ~4 hours
**Impact:** High - testability, flexibility

#### R2.2: Add Test Suite Foundation

**Files:** New `tests/` directory

**Priority Tests:**
1. `tests/services/test_credit_service.py`
2. `tests/services/test_gemini_service.py`
3. `tests/services/test_extraction_service.py`
4. `tests/repositories/test_recipe_repository.py`

**Effort:** ~1-2 days
**Impact:** High - catch bugs, enable refactoring

#### R2.3: Extract Progress Callback Helper

**File:** `extraction_service.py`

**Change:**
```python
def _create_progress_callback(
    self,
    job_id: Optional[str],
    external_callback: Optional[Callable],
    scale_factor: float = 0.7
) -> Callable[[int, str], None]:
    def callback(percentage: int, step: str):
        scaled = int(percentage * scale_factor)
        if external_callback:
            external_callback(scaled, step)
        if job_id:
            asyncio.create_task(
                self._safe_update_job_status(job_id, scaled, step)
            )
    return callback
```

**Effort:** ~1 hour
**Impact:** Medium - reduces duplication

### 6.3 Priority 3: Medium (Plan For)

#### R3.1: Split Large Services

**Current:**
- `extraction_service.py` - 1,261 lines
- `moderation_service.py` - 55KB

**Target Structure:**
```
services/
├── extraction/
│   ├── __init__.py
│   ├── orchestrator.py      # Main extraction flow
│   ├── job_manager.py       # Job CRUD operations
│   ├── duplicate_checker.py # Duplicate detection
│   └── progress_tracker.py  # Progress updates
```

**Effort:** ~4-6 hours
**Impact:** Medium - maintainability

#### R3.2: Add Circuit Breaker

**Files:** New `core/circuit_breaker.py`

```python
from pybreaker import CircuitBreaker

gemini_circuit = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    exclude=[NotARecipeError]  # Don't count as failures
)
```

**Effort:** ~2 hours
**Impact:** Medium - resilience

#### R3.3: Add Structured Logging

**Files:** `core/logging_config.py`, all services

**Change:**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "extraction_complete",
    source_type=source_type,
    duration_seconds=duration,
    cost_usd=cost,
    success=True
)
```

**Effort:** ~3-4 hours
**Impact:** Medium - observability

### 6.4 Priority 4: Low (Nice to Have)

- Move model names to configuration
- Add extraction metrics dashboard
- Implement request correlation IDs
- Add caching layer for category lookups
- Split large endpoint files

---

## 7. Ideal Rewrite Architecture

If the extraction system were to be completely rewritten, here's the recommended architecture:

### 7.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│  (FastAPI with rate limiting, auth, request validation)         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Job Orchestrator                              │
│  (Creates jobs, manages state machine, handles retries)         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Message Queue                                │
│  (Redis Streams / Celery / AWS SQS)                             │
│  - Decouples API from processing                                │
│  - Enables horizontal scaling                                    │
│  - Built-in retry and dead-letter queues                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    Worker 1   │ │    Worker 2   │ │    Worker N   │
│  (Extractor)  │ │  (Extractor)  │ │  (Extractor)  │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └────────────────┼─────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Services                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ AI Service  │ │Image Service│ │Storage Svc  │               │
│  │ (Gemini/   │ │ (Flux)      │ │ (Supabase)  │               │
│  │  OpenAI)   │ │             │ │             │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Key Design Changes

#### Change 1: Message Queue for Extraction Jobs

**Why:** Current `BackgroundTasks` approach:
- Loses jobs on server restart
- Can't scale horizontally
- No built-in retry

**Recommended:** Redis Streams or Celery:
```python
# Producer (API endpoint)
await redis.xadd("extraction_jobs", {
    "job_id": job_id,
    "user_id": user_id,
    "source_type": source_type,
    "source": source
})

# Consumer (Worker)
async def process_extraction_jobs():
    while True:
        jobs = await redis.xread({"extraction_jobs": ">"}, block=5000)
        for job in jobs:
            await extract_recipe(job)
```

#### Change 2: State Machine for Job Status

**Why:** Current approach manually manages status transitions.

**Recommended:** Explicit state machine:
```python
from transitions import Machine

class ExtractionJob:
    states = ['pending', 'downloading', 'processing', 'normalizing',
              'saving', 'completed', 'failed', 'cancelled']

    transitions = [
        {'trigger': 'start', 'source': 'pending', 'dest': 'downloading'},
        {'trigger': 'download_complete', 'source': 'downloading', 'dest': 'processing'},
        {'trigger': 'process_complete', 'source': 'processing', 'dest': 'normalizing'},
        # ...
    ]
```

#### Change 3: Plugin-Based Extractors

**Why:** Adding new extractors requires modifying `ExtractionService`.

**Recommended:** Registry pattern:
```python
class ExtractorRegistry:
    _extractors: Dict[SourceType, Type[BaseExtractor]] = {}

    @classmethod
    def register(cls, source_type: SourceType):
        def decorator(extractor_cls):
            cls._extractors[source_type] = extractor_cls
            return extractor_cls
        return decorator

    @classmethod
    def get(cls, source_type: SourceType) -> BaseExtractor:
        return cls._extractors[source_type]()

@ExtractorRegistry.register(SourceType.VIDEO)
class VideoExtractor(BaseExtractor):
    pass
```

#### Change 4: Proper Repository Pattern with Unit of Work

**Why:** Current repositories don't support transactions.

**Recommended:**
```python
class UnitOfWork:
    def __init__(self, session):
        self.session = session
        self.recipes = RecipeRepository(session)
        self.video_sources = VideoSourceRepository(session)

    async def __aenter__(self):
        await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()

# Usage
async with UnitOfWork(db) as uow:
    recipe = await uow.recipes.create(data)
    await uow.video_sources.create(video_data)
    # Atomic commit
```

#### Change 5: Event-Driven Architecture

**Why:** Current progress updates are tightly coupled.

**Recommended:**
```python
class EventBus:
    async def publish(self, event: Event):
        for handler in self._handlers[type(event)]:
            await handler(event)

@dataclass
class ExtractionProgressEvent(Event):
    job_id: str
    progress: int
    step: str

# Handlers
async def update_database(event: ExtractionProgressEvent):
    await job_repo.update_progress(event.job_id, event.progress)

async def notify_sse(event: ExtractionProgressEvent):
    await broadcaster.publish(event.job_id, event.to_dict())
```

### 7.3 Rewrite Effort Estimate

| Component | Effort | Priority |
|-----------|--------|----------|
| Message queue integration | 2-3 days | High |
| State machine implementation | 1-2 days | Medium |
| Plugin-based extractors | 1 day | Low |
| Unit of Work pattern | 2-3 days | Medium (requires DB change) |
| Event-driven progress | 1-2 days | Medium |
| **Total Rewrite** | **1-2 weeks** | - |

**Recommendation:** Incremental refactoring is preferred over full rewrite. The current architecture is solid; address the specific issues identified in Priority 1-2 recommendations first.

---

## Summary

### Current State Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Architecture | **B+** | Clean Architecture, well-structured |
| Code Quality | **B** | Good patterns, some issues |
| Extraction Process | **A-** | Robust, cost-effective |
| Performance | **B** | Good async design, room for improvement |
| Testability | **D** | Missing test coverage |
| Maintainability | **B** | Clear structure, some large files |

### Recommended Actions

1. **Immediate (This Week):**
   - Add retry logic to external APIs
   - Add request timeouts
   - Fix async repository methods

2. **Short-term (Next 2 Weeks):**
   - Implement dependency injection
   - Create test suite foundation
   - Remove debug logging

3. **Medium-term (Next Month):**
   - Split large services
   - Add circuit breaker
   - Implement structured logging

4. **Long-term (Quarter):**
   - Consider message queue for extraction jobs
   - Add metrics dashboard
   - Full test coverage

The codebase is in good shape overall. The architecture was well-chosen and has scaled reasonably well. Focus on the specific improvements identified rather than a full rewrite.
