# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server with auto-reload
python main.py

# Run tests
pytest
pytest -v                           # verbose
pytest path/to/test_file.py         # single file
pytest -k "test_name"               # specific test by name
pytest --cov=app                    # with coverage

# Install dependencies
pip install -r requirements.txt
```

### System Dependencies

```bash
# macOS
brew install ffmpeg tesseract

# Linux
sudo apt-get install ffmpeg tesseract-ocr
```

## Architecture

This is a **Clean Architecture** FastAPI backend with strict layer separation:

```
app/
├── api/v1/          # HTTP layer: routes, request/response schemas
│   ├── endpoints/   # Route handlers (auth, recipes, cookbooks, extraction, upload)
│   └── schemas/     # Pydantic request/response models
├── core/            # Infrastructure: app factory, config, database, security
├── domain/          # Business entities and enums (framework-agnostic)
├── repositories/    # Data access layer (Supabase operations)
└── services/        # Business logic and orchestration
    └── extractors/  # Source-specific extraction (video, photo, voice, link, paste)
```

**Dependency flow**: API → Services → Repositories → Database

## Key Files

- `main.py` - Entry point, creates FastAPI app via `create_app()`
- `app/core/config.py` - Settings class with all env vars (`get_settings()`)
- `app/core/security.py` - Auth utilities (`get_current_user`, `get_current_user_optional`)
- `app/core/database.py` - Supabase client (`get_supabase_client`)
- `app/api/v1/router.py` - Aggregates all endpoint routers

## Extraction Flow

The core feature is AI-powered recipe extraction:

1. User submits content → `POST /api/v1/extraction/submit`
2. `ExtractionService` creates job, selects extractor by `SourceType`
3. Extractor processes content:
   - **Video**: yt-dlp download → audio extraction → Whisper transcription → frame OCR
   - **Photo**: Tesseract OCR + GPT-4 Vision
   - **Voice**: Whisper transcription
   - **Link**: BeautifulSoup scraping + schema.org parsing
   - **Paste**: Text normalization
4. `OpenAIService.normalize_recipe()` structures raw content
5. Recipe saved via `RecipeRepository`
6. Job status updated to `COMPLETED`

## Adding Features

### New API Endpoint

1. Define schemas in `app/api/v1/schemas/`
2. Create handler in `app/api/v1/endpoints/`
3. Register in `app/api/v1/router.py`
4. Add service logic if needed in `app/services/`
5. Add repository methods in `app/repositories/`

### New Extractor

1. Create class in `app/services/extractors/` inheriting `BaseExtractor`
2. Implement `async def extract(self, source: str, **kwargs) -> Dict[str, Any]`
3. Add to `SourceType` enum in `app/domain/enums.py`
4. Register in `ExtractionService._get_extractor()`

## Important Patterns

- **Dependency Injection**: Use FastAPI's `Depends()` for auth and DB client
- **Async/Await**: All database operations are async
- **Background Tasks**: Long-running extraction uses FastAPI BackgroundTasks
- **RLS**: Supabase Row-Level Security enforces data access - always pass user context
- **JSONB**: Ingredients and instructions stored as JSONB arrays for flexibility

## Environment Variables

Required in `.env` (see `.env.example`):

```
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
OPENAI_API_KEY=
OPENAI_ORGANIZATION_ID=
OPENAI_PROJECT_ID=
```

## API Documentation

When server is running:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
