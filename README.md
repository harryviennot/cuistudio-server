# Recipe App Backend

A clean, well-architected FastAPI backend for a recipe management application with AI-powered recipe extraction from multiple sources.

## Features

### Recipe Management

- Create, read, update, and delete recipes
- Support for multiple source types:
  - Video (TikTok, Instagram Reels, YouTube Shorts)
  - Photos (with OCR and GPT-4 Vision)
  - Voice recordings (transcribed via Whisper)
  - URLs (web scraping)
  - Smart paste (raw text normalization)

### Recipe Organization

- Cookbooks (recipe collections)
- Nested folder structure
- Tag and category system
- User-specific customizations (ratings, notes, custom cook times)

### Social Features

- Recipe forking with attribution chains
- Sharing recipes and cookbooks with specific users
- Permission levels (view, fork, collaborate)
- Fork tracking and visibility

### AI-Powered Features

- Automatic recipe normalization and gap-filling using GPT-4
- Natural language recipe search
- Image analysis for photo-based extraction
- Intelligent recipe parsing from unstructured content

### Authentication & Security

- Supabase Auth integration
- JWT-based authentication
- Row-level security (RLS)
- User-specific data privacy

## Architecture

This project follows **Clean Architecture** principles with clear separation of concerns:

```
app/
├── api/              # API layer (request/response schemas, routes)
├── core/             # Core configuration (app, config, security, database)
├── domain/           # Domain models and business rules
├── repositories/     # Data access layer
├── services/         # Business logic and external integrations
└── utils/            # Utility functions
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Prerequisites

- Python 3.11+
- Supabase account
- OpenAI API key
- FFmpeg (for video processing)
- Tesseract OCR (for image text extraction)

### Installing Dependencies (macOS)

```bash
# Install FFmpeg
brew install ffmpeg

# Install Tesseract
brew install tesseract
```

### Installing Dependencies (Linux)

```bash
# Install FFmpeg
sudo apt-get install ffmpeg

# Install Tesseract
sudo apt-get install tesseract-ocr
```

## Setup

### 1. Clone and Navigate

```bash
cd new-backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Run the database schema from `database/schema.sql` in the Supabase SQL Editor
3. Set up storage bucket for images (see `database/README.md`)

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_PUBLISHABLE_KEY=your_publishable_key
SUPABASE_SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
```

### 6. Run the Application

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Project Structure

```
new-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API route handlers
│   │       │   ├── auth.py
│   │       │   ├── recipes.py
│   │       │   ├── cookbooks.py
│   │       │   └── extraction.py
│   │       ├── schemas/        # Request/response schemas
│   │       └── router.py       # Main API router
│   ├── core/
│   │   ├── app.py             # FastAPI app factory
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Supabase client
│   │   ├── security.py        # Authentication utilities
│   │   └── logging_config.py  # Logging setup
│   ├── domain/
│   │   ├── enums.py           # Domain enumerations
│   │   └── models.py          # Domain models (entities)
│   ├── repositories/
│   │   ├── base.py            # Base repository
│   │   ├── recipe_repository.py
│   │   ├── user_recipe_repository.py
│   │   └── cookbook_repository.py
│   ├── services/
│   │   ├── openai_service.py  # AI integration
│   │   ├── extraction_service.py  # Extraction orchestrator
│   │   └── extractors/        # Source-specific extractors
│   │       ├── video_extractor.py
│   │       ├── photo_extractor.py
│   │       ├── voice_extractor.py
│   │       ├── url_extractor.py
│   │       └── paste_extractor.py
│   └── __init__.py
├── database/
│   ├── schema.sql             # Database schema
│   └── README.md              # Database setup guide
├── docs/
│   ├── ARCHITECTURE.md        # Architecture documentation
│   └── DEVELOPER_GUIDE.md     # Guide for adding features
├── temp/                      # Temporary files (videos, frames)
├── .env.example
├── .gitignore
├── main.py                    # Application entry point
├── requirements.txt
└── README.md
```

## Usage Examples

### Authentication

```bash
# Sign up
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### Extract Recipe from Video

```bash
curl -X POST http://localhost:8000/api/v1/extraction/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "source_type": "video",
    "source_url": "https://www.tiktok.com/@user/video/123456"
  }'
```

### Search Recipes

```bash
curl -X POST http://localhost:8000/api/v1/recipes/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "quick pasta recipe under 20 minutes",
    "limit": 10
  }'
```

### Fork a Recipe

```bash
curl -X POST http://localhost:8000/api/v1/recipes/{recipe_id}/fork \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "My Modified Version",
    "is_public": true
  }'
```

## Development

### Adding a New Feature

See [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for detailed instructions on:

- Adding new endpoints
- Creating new extractors
- Extending domain models
- Writing tests

### Code Style

This project follows:

- PEP 8 style guide
- Type hints for better IDE support
- Comprehensive docstrings
- Clean architecture principles

### Logging

Logs are configured in `app/core/logging_config.py`. Adjust log level in `.env`:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Deployment

### Using Docker (Coming Soon)

```bash
docker build -t recipe-app-backend .
docker run -p 8000:8000 --env-file .env recipe-app-backend
```

### Manual Deployment

1. Set up production environment variables
2. Set `APP_ENV=production` in `.env`
3. Use a production ASGI server:

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Contributing

1. Follow the clean architecture patterns established in the codebase
2. Add comprehensive docstrings
3. Update tests for new features
4. Update documentation

## License

MIT License

## Support

For issues and questions:

- Check the [documentation](docs/)
- Review existing issues
- Create a new issue with detailed information

## Roadmap

- [ ] WebSocket support for real-time extraction progress
- [ ] Recipe versioning system
- [ ] Advanced search with filters
- [ ] Recipe recommendations
- [ ] Meal planning features
- [ ] Grocery list generation
- [ ] Unit conversion utilities
- [ ] Multi-language support
