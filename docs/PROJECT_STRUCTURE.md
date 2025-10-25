# Project Structure

This document describes the organization of the cuistudio-server codebase.

## Directory Structure

```
cuistudio-server/
├── app/                      # Main application package
│   ├── __init__.py          # App package initialization
│   ├── auth.py              # Authentication utilities and dependencies
│   ├── config.py            # Application configuration and settings
│   ├── database.py          # Database client initialization
│   │
│   ├── models/              # Pydantic models (data schemas)
│   │   ├── __init__.py      # Export all models
│   │   ├── auth.py          # Authentication request/response models
│   │   ├── common.py        # Shared models and enums
│   │   ├── recipe.py        # Recipe-related models
│   │   └── user.py          # User models
│   │
│   ├── routers/             # API route handlers
│   │   ├── __init__.py      # Router package initialization
│   │   └── auth.py          # Authentication endpoints
│   │
│   ├── extraction/          # Recipe extraction pipeline
│   │   └── ...              # Extraction-related modules
│   │
│   └── utils/               # Utility functions
│       └── ...              # Helper utilities
│
├── docs/                     # Documentation
│   ├── AUTHENTICATION.md     # Authentication API documentation
│   └── PROJECT_STRUCTURE.md  # This file
│
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
├── env.example               # Example environment variables
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Docker compose configuration
└── debug_test.py            # Debug and testing utilities
```

## Module Organization

### `/app/models/` - Data Models

Organized by domain, each file contains related Pydantic models:

- **`common.py`** - Shared models and enums

  - `SourceType` - Enum for recipe sources (video, image, text)
  - `JobStatus` - Enum for processing job status
  - `MessageResponse` - Generic message response

- **`user.py`** - User-related models

  - `UserResponse` - User information response

- **`auth.py`** - Authentication models

  - `SignUpRequest` - User registration
  - `LoginRequest` - User login
  - `AuthResponse` - Authentication response with tokens
  - `PasswordResetRequest` - Password reset request
  - `PasswordUpdateRequest` - Password update
  - `RefreshTokenRequest` - Token refresh

- **`recipe.py`** - Recipe-related models
  - `RecipeBase` - Base recipe model
  - `RecipeCreate` - Create recipe request
  - `RecipeUpdate` - Update recipe request
  - `RecipeResponse` - Recipe response with metadata
  - `RecipeSubmission` - Recipe submission for processing
  - `RatingBase`, `RatingCreate`, `RatingResponse` - Rating models
  - `ParsingJobResponse` - Parsing job status

### `/app/routers/` - API Endpoints

Each router module groups related endpoints:

- **`auth.py`** - Authentication endpoints
  - `POST /auth/signup` - Register new user
  - `POST /auth/login` - Authenticate user
  - `POST /auth/logout` - Logout user
  - `GET /auth/me` - Get current user
  - `POST /auth/refresh` - Refresh access token
  - `POST /auth/password-reset` - Request password reset
  - `POST /auth/password-update` - Update password
  - `POST /auth/verify-token` - Verify token validity

### Core Files

- **`main.py`** - FastAPI application setup

  - App initialization
  - CORS configuration
  - Router registration
  - Health check endpoints

- **`config.py`** - Configuration management

  - Environment variable loading
  - Settings validation
  - Application constants

- **`database.py`** - Database client

  - Supabase client initialization
  - Database connection dependency

- **`auth.py`** - Authentication utilities
  - `get_current_user()` - JWT token verification dependency
  - User authentication helpers

## Import Conventions

### Importing Models

```python
# Import specific models from their module
from app.models.auth import SignUpRequest, LoginRequest
from app.models.user import UserResponse
from app.models.common import SourceType, MessageResponse

# Or import from the models package (recommended)
from app.models import (
    SignUpRequest,
    LoginRequest,
    UserResponse,
    SourceType,
    MessageResponse
)
```

### Importing Routers

```python
# Import router modules
from app.routers import auth

# Register in main.py
app.include_router(auth.router)
```

### Importing Configuration

```python
from app.config import settings

# Access settings
supabase_url = settings.SUPABASE_URL
```

### Importing Dependencies

```python
from fastapi import Depends
from app.database import get_supabase_client
from app.auth import get_current_user

# Use in route handlers
async def my_route(
    supabase: Client = Depends(get_supabase_client),
    user: dict = Depends(get_current_user)
):
    pass
```

## Design Principles

### 1. Separation of Concerns

- Models define data structures
- Routers handle HTTP requests/responses
- Services contain business logic
- Utils provide reusable helpers

### 2. Modularity

- Each module has a single responsibility
- Related functionality is grouped together
- Easy to locate and modify specific features

### 3. Scalability

- New features can be added without modifying existing code
- Easy to add new routers, models, or services
- Clear patterns for extending functionality

### 4. Maintainability

- Clear file organization
- Consistent naming conventions
- Comprehensive documentation
- Type hints throughout

## Adding New Features

### Adding a New Model

1. Create model in appropriate file under `app/models/`
2. Export from `app/models/__init__.py`
3. Use in routers or services as needed

Example:

```python
# app/models/cookbook.py
from pydantic import BaseModel

class CookbookCreate(BaseModel):
    title: str
    description: str

# app/models/__init__.py
from app.models.cookbook import CookbookCreate

__all__ = [
    # ... existing exports
    "CookbookCreate",
]
```

### Adding a New Router

1. Create router file in `app/routers/`
2. Define APIRouter with prefix and tags
3. Add route handlers
4. Register in `main.py`

Example:

```python
# app/routers/cookbooks.py
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/cookbooks",
    tags=["cookbooks"]
)

@router.get("/")
async def list_cookbooks():
    return {"cookbooks": []}

# main.py
from app.routers import auth, cookbooks

app.include_router(auth.router)
app.include_router(cookbooks.router)
```

### Adding a New Service

1. Create service file in `app/services/`
2. Implement business logic
3. Use in routers via dependency injection

Example:

```python
# app/services/cookbook_service.py
from supabase import Client

class CookbookService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_cookbook(self, data):
        # Business logic here
        pass

# app/routers/cookbooks.py
from app.services.cookbook_service import CookbookService

@router.post("/")
async def create_cookbook(
    supabase: Client = Depends(get_supabase_client)
):
    service = CookbookService(supabase)
    # Use service methods
```

## Environment Setup

### Required Environment Variables

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your-anon-key

# OpenAI
OPENAI_API_KEY=your-key
OPENAI_ORGANIZATION_ID=your-org-id
OPENAI_PROJECT_ID=your-project-id

# App Settings
DEBUG=False
```

See `env.example` for a complete list.

## Running the Application

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use Python directly
python main.py
```

### Production

```bash
# Using Docker
docker-compose up -d

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Documentation

Once running, access:

- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

## Testing

```bash
# Run debug tests
python debug_test.py

# Run specific test functions
python -c "from debug_test import test_database_connection; import asyncio; asyncio.run(test_database_connection())"
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Document classes and functions with docstrings
- Keep functions focused and small
- Use descriptive variable names

## Version Control

Excluded from Git (see `.gitignore`):

- `__pycache__/` - Python bytecode
- `venv/` - Virtual environment
- `.env` - Environment variables
- `*.pyc` - Compiled Python files
- `downloads/` - Downloaded content
- `frames/` - Extracted video frames

## Future Improvements

- [ ] Add comprehensive test suite (pytest)
- [ ] Implement service layer for business logic
- [ ] Add database migration management
- [ ] Create CLI tools for common tasks
- [ ] Add API rate limiting
- [ ] Implement caching layer
- [ ] Add monitoring and logging
- [ ] Create admin dashboard

