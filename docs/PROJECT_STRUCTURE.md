# Project Structure

Complete file tree of the Recipe App Backend.

```
new-backend/
│
├── 📄 .env                          # Environment variables (DO NOT COMMIT)
├── 📄 .env.example                  # Environment variables template
├── 📄 .gitignore                    # Git ignore rules
├── 📄 main.py                       # Application entry point
├── 📄 requirements.txt              # Python dependencies
│
├── 📄 README.md                     # Main documentation
├── 📄 QUICKSTART.md                 # Quick start guide
├── 📄 IMPLEMENTATION_SUMMARY.md     # Implementation overview
├── 📄 PROJECT_STRUCTURE.md          # This file
│
├── 📁 app/                          # Main application code
│   ├── 📄 __init__.py
│   │
│   ├── 📁 api/                      # API Layer
│   │   ├── 📄 __init__.py
│   │   └── 📁 v1/                   # API Version 1
│   │       ├── 📄 __init__.py
│   │       ├── 📄 router.py         # Main API router
│   │       │
│   │       ├── 📁 endpoints/        # Route Handlers
│   │       │   ├── 📄 __init__.py
│   │       │   ├── 📄 auth.py       # Authentication endpoints
│   │       │   ├── 📄 recipes.py    # Recipe endpoints (CRUD, fork, search)
│   │       │   ├── 📄 cookbooks.py  # Cookbook endpoints
│   │       │   └── 📄 extraction.py # Extraction endpoints
│   │       │
│   │       └── 📁 schemas/          # Request/Response Models
│   │           ├── 📄 __init__.py
│   │           ├── 📄 common.py     # Shared schemas (MessageResponse, etc.)
│   │           ├── 📄 auth.py       # Auth schemas
│   │           ├── 📄 recipe.py     # Recipe schemas
│   │           ├── 📄 cookbook.py   # Cookbook schemas
│   │           └── 📄 extraction.py # Extraction schemas
│   │
│   ├── 📁 core/                     # Core Infrastructure
│   │   ├── 📄 __init__.py
│   │   ├── 📄 app.py                # FastAPI application factory
│   │   ├── 📄 config.py             # Configuration management
│   │   ├── 📄 database.py           # Supabase client setup
│   │   ├── 📄 security.py           # Authentication & authorization
│   │   └── 📄 logging_config.py     # Logging configuration
│   │
│   ├── 📁 domain/                   # Domain Layer (Business Entities)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 models.py             # Domain models (Recipe, Cookbook, etc.)
│   │   └── 📄 enums.py              # Enumerations (SourceType, etc.)
│   │
│   ├── 📁 repositories/             # Data Access Layer
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py               # Base repository with common CRUD
│   │   ├── 📄 recipe_repository.py  # Recipe database operations
│   │   ├── 📄 user_recipe_repository.py  # User-specific recipe data
│   │   └── 📄 cookbook_repository.py     # Cookbook database operations
│   │
│   └── 📁 services/                 # Business Logic Layer
│       ├── 📄 __init__.py
│       ├── 📄 openai_service.py     # OpenAI/AI integration service
│       ├── 📄 extraction_service.py # Extraction orchestration
│       │
│       └── 📁 extractors/           # Recipe Extractors
│           ├── 📄 __init__.py
│           ├── 📄 base_extractor.py      # Base extractor class
│           ├── 📄 video_extractor.py     # TikTok, Reels, Shorts
│           ├── 📄 photo_extractor.py     # Image OCR + GPT-4 Vision
│           ├── 📄 voice_extractor.py     # Voice recording transcription
│           ├── 📄 url_extractor.py       # Web scraping
│           └── 📄 paste_extractor.py     # Smart copy/paste
│
├── 📁 database/                     # Database Schema & Migrations
│   ├── 📄 README.md                 # Database setup guide
│   └── 📄 schema.sql                # Complete database schema
│
├── 📁 docs/                         # Documentation
│   ├── 📄 ARCHITECTURE.md           # Architecture documentation
│   └── 📄 DEVELOPER_GUIDE.md        # Developer guide for adding features
│
├── 📁 temp/                         # Temporary Files (gitignored)
│   ├── 📁 videos/                   # Downloaded videos
│   └── 📁 frames/                   # Extracted video frames
│
└── 📁 tests/                        # Test Suite (to be implemented)
    ├── 📄 conftest.py               # Test configuration
    ├── 📁 unit/                     # Unit tests
    └── 📁 integration/              # Integration tests
```

## File Count Summary

```
Total Files: ~40 Python files
Lines of Code: ~8,000+ lines
Documentation: ~3,000+ lines
```

## Key Directories

### `/app/api/v1/endpoints/`

Contains all API route handlers. Each file corresponds to a resource:

- `auth.py` - User authentication and authorization
- `recipes.py` - Recipe CRUD, forking, searching
- `cookbooks.py` - Cookbook and folder management
- `extraction.py` - Recipe extraction job handling

### `/app/services/`

Business logic and external integrations:

- `openai_service.py` - AI-powered recipe processing
- `extraction_service.py` - Coordinates extraction from multiple sources
- `extractors/` - Source-specific extraction implementations

### `/app/repositories/`

Database operations abstraction:

- `base.py` - Common CRUD operations
- Specific repositories for each domain entity

### `/app/domain/`

Core business entities and rules:

- `models.py` - Pydantic models for business entities
- `enums.py` - Domain-specific enumerations

### `/database/`

Database schema and setup:

- `schema.sql` - Complete PostgreSQL schema with RLS policies
- `README.md` - Database setup instructions

## Configuration Files

- `.env` - Environment variables (contains secrets)
- `.env.example` - Template for environment variables
- `.gitignore` - Files to exclude from version control
- `requirements.txt` - Python package dependencies

## Documentation Files

- `README.md` - Project overview, features, setup
- `QUICKSTART.md` - Get started in 5 minutes
- `ARCHITECTURE.md` - Detailed architecture explanation
- `DEVELOPER_GUIDE.md` - How to add new features
- `IMPLEMENTATION_SUMMARY.md` - Complete implementation overview
- `PROJECT_STRUCTURE.md` - This file

## Entry Points

### Main Application

```bash
python main.py
```

- Starts the FastAPI server
- Loads configuration
- Sets up logging
- Includes all routers

### API Documentation

```
http://localhost:8000/api/docs       # Swagger UI
http://localhost:8000/api/redoc      # ReDoc
```

## Import Paths

### Example Imports

```python
# Configuration
from app.core.config import get_settings

# Database
from app.core.database import get_supabase_client

# Security
from app.core.security import get_current_user

# Domain Models
from app.domain.models import Recipe, Cookbook
from app.domain.enums import SourceType, DifficultyLevel

# Repositories
from app.repositories.recipe_repository import RecipeRepository

# Services
from app.services.openai_service import OpenAIService
from app.services.extraction_service import ExtractionService

# Schemas
from app.api.v1.schemas.recipe import RecipeResponse, RecipeCreateRequest
```

## Directory Conventions

### Naming

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_CASE`

### Organization

- One main class per file
- Related schemas grouped together
- Endpoints organized by resource
- Services organized by responsibility

## Growth Path

As the project grows, you can add:

```
app/
├── services/
│   ├── meal_plan_service.py     # New feature: meal planning
│   ├── grocery_list_service.py  # New feature: grocery lists
│   └── recommendation_service.py # New feature: recommendations
│
├── repositories/
│   ├── meal_plan_repository.py
│   └── grocery_list_repository.py
│
└── api/v1/endpoints/
    ├── meal_plans.py
    └── grocery_lists.py
```

## Testing Structure (Future)

```
tests/
├── conftest.py                 # Shared test fixtures
│
├── unit/                       # Fast, isolated tests
│   ├── test_openai_service.py
│   ├── test_extractors.py
│   └── test_repositories.py
│
├── integration/                # Multi-component tests
│   ├── test_recipe_api.py
│   ├── test_extraction_flow.py
│   └── test_cookbook_api.py
│
└── e2e/                        # End-to-end tests
    └── test_user_workflows.py
```

## Code Metrics

### Repository Layer

- 4 repository classes
- ~500 lines of code
- Covers all database operations

### Service Layer

- 2 main services
- 5 extractors
- ~1,500 lines of code
- Handles all business logic

### API Layer

- 4 endpoint files
- 30+ routes
- ~2,000 lines of code
- Full REST API

### Domain Layer

- 15+ domain models
- 10+ enumerations
- ~800 lines of code

## Dependencies

### Production Dependencies

- FastAPI (web framework)
- Supabase (database, auth, storage)
- OpenAI (AI services)
- yt-dlp (video downloading)
- Tesseract/Pillow (image processing)
- Beautiful Soup (web scraping)

### Development Dependencies

- pytest (testing)
- black (code formatting)
- mypy (type checking)
- flake8 (linting)

## Next Steps

1. **Run the application**: `python main.py`
2. **Read the documentation**: Start with QUICKSTART.md
3. **Explore the code**: Follow the structure above
4. **Add features**: Use DEVELOPER_GUIDE.md
5. **Deploy**: See README.md deployment section

## Maintenance

### Adding Files

- Place in appropriate directory
- Follow naming conventions
- Update imports
- Add to documentation if needed

### Removing Files

- Check for dependencies
- Update imports
- Remove from routers/services
- Update documentation

### Refactoring

- Keep layer separation
- Maintain consistent patterns
- Update tests
- Update documentation
