# Developer Guide

This guide will help you add new features and extend the Recipe App Backend.

## Table of Contents

1. [Adding a New API Endpoint](#adding-a-new-api-endpoint)
2. [Creating a New Extractor](#creating-a-new-extractor)
3. [Extending Domain Models](#extending-domain-models)
4. [Adding Database Tables](#adding-database-tables)
5. [Implementing New Services](#implementing-new-services)
6. [Testing Your Code](#testing-your-code)
7. [Best Practices](#best-practices)

---

## Adding a New API Endpoint

### Step 1: Define Request/Response Schemas

Create schemas in `app/api/v1/schemas/`:

```python
# app/api/v1/schemas/my_feature.py
from pydantic import BaseModel
from typing import Optional

class MyFeatureCreateRequest(BaseModel):
    """Request schema for creating my feature"""
    name: str
    description: Optional[str] = None

class MyFeatureResponse(BaseModel):
    """Response schema for my feature"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
```

### Step 2: Create Endpoint Handler

Create endpoint file in `app/api/v1/endpoints/`:

```python
# app/api/v1/endpoints/my_feature.py
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_supabase_client
from app.core.security import get_current_user
from app.api.v1.schemas.my_feature import (
    MyFeatureCreateRequest,
    MyFeatureResponse
)

router = APIRouter(prefix="/my-feature", tags=["My Feature"])

@router.post("", response_model=MyFeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_my_feature(
    data: MyFeatureCreateRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new feature instance"""
    try:
        # Your logic here
        result = supabase.table("my_feature").insert({
            "name": data.name,
            "description": data.description,
            "user_id": current_user["id"]
        }).execute()

        return MyFeatureResponse(**result.data[0])

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

### Step 3: Register Router

Add to `app/api/v1/router.py`:

```python
from app.api.v1.endpoints import auth, recipes, cookbooks, extraction, my_feature

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(recipes.router)
api_router.include_router(cookbooks.router)
api_router.include_router(extraction.router)
api_router.include_router(my_feature.router)  # Add this line
```

### Step 4: Test

```bash
curl -X POST http://localhost:8000/api/v1/my-feature \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "Test", "description": "Testing"}'
```

---

## Creating a New Extractor

### Step 1: Create Extractor Class

Create file in `app/services/extractors/`:

```python
# app/services/extractors/my_source_extractor.py
from typing import Dict, Any
import logging

from app.services.extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class MySourceExtractor(BaseExtractor):
    """Extract recipes from my custom source"""

    async def extract(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Extract recipe content from source

        Args:
            source: Source URL or content

        Returns:
            Dict with 'text' key containing extracted content
        """
        try:
            self.update_progress(20, "Fetching content")

            # Your extraction logic here
            raw_content = await self._fetch_content(source)

            self.update_progress(70, "Processing content")

            # Process the content
            processed = await self._process(raw_content)

            self.update_progress(100, "Extraction complete")

            return {
                "text": processed,
                "source_url": source
            }

        except Exception as e:
            logger.error(f"Error extracting from source: {str(e)}")
            raise

    async def _fetch_content(self, source: str) -> str:
        """Fetch content from source"""
        # Implementation
        pass

    async def _process(self, content: str) -> str:
        """Process raw content"""
        # Implementation
        pass
```

### Step 2: Add to SourceType Enum

Update `app/domain/enums.py`:

```python
class SourceType(str, Enum):
    VIDEO = "video"
    PHOTO = "photo"
    VOICE = "voice"
    URL = "url"
    PASTE = "paste"
    MY_SOURCE = "my_source"  # Add this
```

### Step 3: Register in Extraction Service

Update `app/services/extraction_service.py`:

```python
from app.services.extractors.my_source_extractor import MySourceExtractor

class ExtractionService:
    def _get_extractor(self, source_type: SourceType, progress_callback=None):
        extractors = {
            SourceType.VIDEO: VideoExtractor,
            SourceType.PHOTO: PhotoExtractor,
            SourceType.VOICE: VoiceExtractor,
            SourceType.URL: URLExtractor,
            SourceType.PASTE: PasteExtractor,
            SourceType.MY_SOURCE: MySourceExtractor,  # Add this
        }
        # ...
```

### Step 4: Test

```python
extractor = MySourceExtractor()
result = await extractor.extract("https://example.com/recipe")
print(result["text"])
```

---

## Extending Domain Models

### Step 1: Update Domain Model

Edit `app/domain/models.py`:

```python
class Recipe(BaseModel):
    # Existing fields...

    # New field
    nutrition_info: Optional[Dict[str, Any]] = None
```

### Step 2: Update Database Schema

Create migration in `database/`:

```sql
-- database/002_add_nutrition_info.sql
ALTER TABLE recipes
ADD COLUMN nutrition_info JSONB DEFAULT NULL;
```

Run in Supabase SQL Editor.

### Step 3: Update Schemas

Update `app/api/v1/schemas/recipe.py`:

```python
class RecipeCreateRequest(BaseModel):
    # Existing fields...
    nutrition_info: Optional[Dict[str, Any]] = None

class RecipeResponse(BaseModel):
    # Existing fields...
    nutrition_info: Optional[Dict[str, Any]] = None
```

### Step 4: Update Repository

If needed, add specific queries in `app/repositories/recipe_repository.py`:

```python
async def get_recipes_by_nutrition(
    self,
    max_calories: int
) -> List[Dict[str, Any]]:
    """Get recipes below calorie threshold"""
    # Implementation
```

---

## Adding Database Tables

### Step 1: Design Schema

```sql
-- database/003_add_meal_plans.sql
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE meal_plan_recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_plan_id UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    meal_date DATE NOT NULL,
    meal_type VARCHAR(20) NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    UNIQUE(meal_plan_id, recipe_id, meal_date, meal_type)
);

-- Indexes
CREATE INDEX idx_meal_plans_user_id ON meal_plans(user_id);
CREATE INDEX idx_meal_plan_recipes_plan_id ON meal_plan_recipes(meal_plan_id);

-- RLS Policies
ALTER TABLE meal_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_plan_recipes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own meal plans" ON meal_plans
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage recipes in their meal plans" ON meal_plan_recipes
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM meal_plans
            WHERE meal_plans.id = meal_plan_recipes.meal_plan_id
            AND meal_plans.user_id = auth.uid()
        )
    );
```

### Step 2: Create Domain Models

```python
# app/domain/models.py
class MealPlan(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    start_date: date
    end_date: date
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MealPlanRecipe(BaseModel):
    id: Optional[str] = None
    meal_plan_id: str
    recipe_id: str
    meal_date: date
    meal_type: str
```

### Step 3: Create Repository

```python
# app/repositories/meal_plan_repository.py
from app.repositories.base import BaseRepository

class MealPlanRepository(BaseRepository):
    def __init__(self, supabase: Client):
        super().__init__(supabase, "meal_plans")

    async def get_user_meal_plans(self, user_id: str):
        # Implementation
        pass
```

### Step 4: Create Service (if needed)

```python
# app/services/meal_plan_service.py
class MealPlanService:
    def __init__(self, supabase: Client):
        self.repo = MealPlanRepository(supabase)

    async def create_meal_plan(self, user_id: str, data: dict):
        # Business logic
        pass
```

### Step 5: Create API Endpoints

Follow the "Adding a New API Endpoint" section above.

---

## Implementing New Services

### When to Create a Service

Create a service when you need:
- Complex business logic
- Operations spanning multiple repositories
- External API integrations
- Workflow orchestration

### Service Template

```python
# app/services/my_service.py
import logging
from typing import Dict, Any, Optional
from supabase import Client

from app.repositories.my_repository import MyRepository

logger = logging.getLogger(__name__)


class MyService:
    """Service for handling my feature logic"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.repo = MyRepository(supabase)

    async def complex_operation(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform complex operation

        Args:
            user_id: User performing the operation
            data: Operation data

        Returns:
            Result dictionary

        Raises:
            ValueError: If validation fails
            Exception: For other errors
        """
        try:
            # 1. Validate input
            self._validate_input(data)

            # 2. Perform operation
            result = await self._do_operation(user_id, data)

            # 3. Update related data
            await self._update_related(result)

            logger.info(f"Operation completed for user {user_id}")

            return result

        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            raise

    def _validate_input(self, data: Dict[str, Any]):
        """Validate input data"""
        # Validation logic
        pass

    async def _do_operation(self, user_id: str, data: Dict[str, Any]):
        """Core operation logic"""
        # Implementation
        pass

    async def _update_related(self, result: Dict[str, Any]):
        """Update related records"""
        # Implementation
        pass
```

---

## Testing Your Code

### Unit Tests

```python
# tests/test_my_service.py
import pytest
from unittest.mock import Mock, AsyncMock

from app.services.my_service import MyService


@pytest.mark.asyncio
async def test_complex_operation():
    # Arrange
    mock_supabase = Mock()
    service = MyService(mock_supabase)

    # Mock repository methods
    service.repo.create = AsyncMock(return_value={"id": "123"})

    # Act
    result = await service.complex_operation("user_123", {"name": "test"})

    # Assert
    assert result["id"] == "123"
    service.repo.create.assert_called_once()
```

### Integration Tests

```python
# tests/integration/test_recipes_api.py
import pytest
from httpx import AsyncClient

from main import app


@pytest.mark.asyncio
async def test_create_recipe():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get auth token
        auth_response = await client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpass"
        })
        token = auth_response.json()["access_token"]

        # Create recipe
        response = await client.post(
            "/api/v1/recipes",
            json={
                "title": "Test Recipe",
                "source_type": "paste",
                "ingredients": [],
                "instructions": []
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        assert response.json()["title"] == "Test Recipe"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_my_service.py

# Run with coverage
pytest --cov=app tests/

# Run with output
pytest -v
```

---

## Best Practices

### Code Organization

1. **Keep layers separated**: Don't call repositories from API endpoints directly
2. **Use dependency injection**: Leverage FastAPI's Depends()
3. **Follow naming conventions**:
   - Functions/methods: `snake_case`
   - Classes: `PascalCase`
   - Constants: `UPPER_CASE`

### Error Handling

```python
try:
    # Your code
    result = await some_operation()
except SpecificException as e:
    # Handle specific exception
    logger.warning(f"Specific issue: {str(e)}")
    raise HTTPException(status_code=400, detail="Specific error message")
except Exception as e:
    # Handle general exception
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical issue")

# Include context
logger.info(f"User {user_id} created recipe {recipe_id}")
```

### Documentation

```python
async def my_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
        HTTPException: When resource not found
    """
    pass
```

### Type Hints

```python
from typing import List, Dict, Optional, Any

async def process_items(
    items: List[str],
    config: Dict[str, Any],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    # Implementation
    pass
```

### Database Queries

```python
# Good: Use parameterized queries (Supabase handles this)
result = supabase.table("recipes").select("*").eq("user_id", user_id).execute()

# Good: Use repository methods
recipes = await recipe_repo.get_user_recipes(user_id)

# Bad: String concatenation (SQL injection risk)
# Don't do this with raw SQL
```

### Performance

1. **Use indexes**: Ensure database queries are optimized with appropriate indexes
2. **Limit data**: Use pagination for list endpoints
3. **Background tasks**: Use for long-running operations
4. **Caching**: Consider caching frequent queries

### Security

1. **Validate input**: Use Pydantic models
2. **Check permissions**: Verify user has access
3. **Sanitize output**: Don't expose sensitive data
4. **Use environment variables**: For secrets and config

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Make changes and commit
git add .
git commit -m "Add my new feature"

# Push to remote
git push origin feature/my-new-feature

# Create pull request
```

### Code Review Checklist

- [ ] Code follows architecture patterns
- [ ] Tests are included
- [ ] Documentation is updated
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate
- [ ] Type hints are used
- [ ] Security is considered
- [ ] Performance is acceptable

---

## Common Patterns

### Pagination

```python
@router.get("/items")
async def list_items(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    items = await repo.list(limit=limit, offset=offset)
    total = await repo.count()

    return {
        "items": items,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit
    }
```

### Optional Authentication

```python
from app.core.security import get_current_user_optional

@router.get("/public-data")
async def get_public_data(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    # Works for both authenticated and anonymous users
    user_id = current_user["id"] if current_user else None
```

### Background Tasks

```python
from fastapi import BackgroundTasks

@router.post("/process")
async def process_data(
    data: MyData,
    background_tasks: BackgroundTasks
):
    # Queue background task
    background_tasks.add_task(long_running_task, data)

    return {"message": "Processing started"}

async def long_running_task(data: MyData):
    # Perform long operation
    pass
```

---

## Getting Help

1. Check existing code for examples
2. Review this guide and ARCHITECTURE.md
3. Consult FastAPI documentation
4. Ask team members
5. Create an issue for bugs or unclear documentation

---

## Contributing

When contributing:
1. Follow the patterns in this guide
2. Write tests for new features
3. Update documentation
4. Keep pull requests focused
5. Respond to code review feedback

Happy coding!
