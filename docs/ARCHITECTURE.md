## Architecture Documentation

This document describes the architecture of the Recipe App Backend.

## Overview

The application follows **Clean Architecture** principles with clear separation between layers:

```
┌─────────────────────────────────────────────┐
│           API Layer (FastAPI)                │
│  - Request/Response Schemas                  │
│  - Route Handlers                            │
│  - Input Validation                          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Service Layer                        │
│  - Business Logic                            │
│  - External Integrations (OpenAI, etc)       │
│  - Orchestration                             │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│       Repository Layer                       │
│  - Data Access                               │
│  - Supabase Operations                       │
│  - Query Building                            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      Database (Supabase/PostgreSQL)          │
│  - Recipes, Cookbooks, Users                 │
│  - Row-Level Security                        │
└─────────────────────────────────────────────┘
```

## Layers

### 1. API Layer (`app/api/`)

**Purpose**: Handle HTTP requests and responses

**Components**:
- **Endpoints** (`v1/endpoints/`): Route handlers organized by resource
- **Schemas** (`v1/schemas/`): Pydantic models for request/response validation
- **Router** (`v1/router.py`): Aggregates all endpoint routers

**Responsibilities**:
- Request validation
- Response formatting
- Authentication checks
- Error handling
- HTTP-specific logic

**Example**:
```python
@router.post("/recipes", response_model=RecipeResponse)
async def create_recipe(
    recipe_data: RecipeCreateRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    # 1. Validate request (automatic via Pydantic)
    # 2. Check authentication
    # 3. Call service/repository
    # 4. Format and return response
```

### 2. Service Layer (`app/services/`)

**Purpose**: Implement business logic and coordinate operations

**Components**:
- **OpenAI Service**: AI-powered recipe processing
- **Extraction Service**: Orchestrates recipe extraction
- **Extractors**: Source-specific extraction logic
  - Video Extractor
  - Photo Extractor
  - Voice Extractor
  - URL Extractor
  - Paste Extractor

**Responsibilities**:
- Business rule enforcement
- Workflow orchestration
- External API integration
- Data transformation
- Complex operations spanning multiple repositories

**Example**:
```python
class ExtractionService:
    async def extract_and_create_recipe(self, user_id, source_type, source):
        # 1. Extract raw content using appropriate extractor
        extractor = self._get_extractor(source_type)
        raw_content = await extractor.extract(source)

        # 2. Normalize with AI
        normalized = self.openai_service.normalize_recipe(raw_content)

        # 3. Save to database
        recipe = await self.recipe_repo.create(normalized)

        # 4. Create contributor record
        # ...

        return recipe
```

### 3. Repository Layer (`app/repositories/`)

**Purpose**: Abstract database operations

**Components**:
- **Base Repository**: Common CRUD operations
- **Recipe Repository**: Recipe-specific queries
- **User Recipe Repository**: User customization data
- **Cookbook Repository**: Cookbook operations
- **Cookbook Folder Repository**: Folder operations

**Responsibilities**:
- Database queries
- Data mapping
- Supabase client interaction
- Transaction management

**Example**:
```python
class RecipeRepository(BaseRepository):
    async def fork_recipe(self, original_id, new_data, user_id):
        # 1. Get original recipe
        original = await self.get_by_id(original_id)

        # 2. Create forked recipe
        forked = await self.create(new_data)

        # 3. Update fork count
        await self.update(original_id, {"fork_count": original["fork_count"] + 1})

        # 4. Create contributor chain
        # ...

        return forked
```

### 4. Domain Layer (`app/domain/`)

**Purpose**: Define core business entities and rules

**Components**:
- **Models** (`models.py`): Business entities (Recipe, Cookbook, etc.)
- **Enums** (`enums.py`): Domain enumerations

**Responsibilities**:
- Entity definitions
- Business rules
- Value objects
- Domain logic

**Example**:
```python
class Recipe(BaseModel):
    title: str
    ingredients: List[Ingredient]
    instructions: List[Instruction]
    timings: Optional[RecipeTimings]
    # ... domain rules embedded in the model

    @field_validator('total_time_minutes')
    def validate_total_time(cls, v, info):
        # Business rule: total time should match prep + cook
        prep = info.data.get('prep_time_minutes')
        cook = info.data.get('cook_time_minutes')
        if prep and cook and not v:
            return prep + cook
        return v
```

### 5. Core Layer (`app/core/`)

**Purpose**: Application infrastructure and configuration

**Components**:
- **App** (`app.py`): FastAPI application factory
- **Config** (`config.py`): Environment configuration
- **Database** (`database.py`): Supabase client setup
- **Security** (`security.py`): Authentication utilities
- **Logging** (`logging_config.py`): Logging configuration

**Responsibilities**:
- Application bootstrap
- Configuration management
- Cross-cutting concerns
- Dependency injection setup

## Data Flow

### Request Flow

```
1. Client Request
   ↓
2. FastAPI receives request
   ↓
3. Middleware (CORS, Auth, etc)
   ↓
4. Route Handler (API Layer)
   ↓
5. Authentication Check (Security)
   ↓
6. Service Layer (Business Logic)
   ↓
7. Repository Layer (Database)
   ↓
8. Supabase/PostgreSQL
   ↓
9. Response (back through layers)
   ↓
10. Client receives formatted response
```

### Extraction Flow

```
1. User submits content for extraction
   ↓
2. Extraction Service creates job
   ↓
3. Background task starts extraction
   ↓
4. Extractor fetches/processes content
   │  ├─ Video: Download → Extract audio → Transcribe → OCR frames
   │  ├─ Photo: OCR → GPT-4 Vision analysis
   │  ├─ Voice: Transcribe with Whisper
   │  ├─ URL: Scrape → Parse schema/text
   │  └─ Paste: Clean text
   ↓
5. OpenAI Service normalizes raw content
   ↓
6. Repository creates recipe in database
   ↓
7. Contributor records created
   ↓
8. Job status updated to "completed"
```

## Database Design

### Key Tables

- **recipes**: Core recipe data
- **recipe_contributors**: Fork attribution chain
- **user_recipe_data**: User customizations
- **cookbooks**: Recipe collections
- **cookbook_folders**: Nested folder structure
- **recipe_shares**: Sharing permissions
- **extraction_jobs**: Track extraction progress

### Row-Level Security

All tables use Supabase RLS policies:
- Users can only access their own data
- Public recipes are viewable by everyone
- Shared recipes are accessible based on permissions
- Collaborators can edit shared content

## External Dependencies

### Supabase
- **Authentication**: JWT-based auth
- **Database**: PostgreSQL with RLS
- **Storage**: Image storage

### OpenAI
- **GPT-4**: Recipe normalization and search
- **Whisper API**: Audio transcription
- **GPT-4 Vision**: Image analysis

### Other Services
- **yt-dlp**: Video downloading
- **Tesseract OCR**: Text extraction from images
- **Beautiful Soup**: Web scraping

## Design Patterns

### 1. Repository Pattern
Abstracts data access logic from business logic.

### 2. Dependency Injection
FastAPI's dependency system for loose coupling.

### 3. Factory Pattern
Application factory (`create_app()`) for flexible setup.

### 4. Strategy Pattern
Different extractors for different source types.

### 5. Template Method
Base extractor with concrete implementations.

## Scalability Considerations

### Current Architecture
- Synchronous request handling
- Background tasks for long-running operations
- Single instance deployment

### Future Scalability

**Horizontal Scaling**:
- Stateless design allows multiple instances
- Shared database (Supabase)
- Load balancer distribution

**Performance Optimizations**:
- Caching layer (Redis) for frequent queries
- Message queue (Celery/RabbitMQ) for extraction jobs
- CDN for image delivery
- Database query optimization

**Monitoring**:
- Application metrics (Prometheus)
- Error tracking (Sentry)
- Performance monitoring (APM tools)

## Security

### Authentication
- Supabase Auth with JWT tokens
- Token validation on protected endpoints
- Refresh token support

### Authorization
- Row-level security policies
- Permission checks in service layer
- Owner and collaborator permissions

### Data Protection
- Environment variables for secrets
- HTTPS in production
- Input validation with Pydantic
- SQL injection prevention (parameterized queries)

### Rate Limiting
- Configurable rate limits
- Per-user tracking
- Protection against abuse

## Error Handling

### Error Flow
```
1. Exception occurs
   ↓
2. Caught by try/except
   ↓
3. Logged with context
   ↓
4. Converted to HTTPException
   ↓
5. FastAPI exception handler
   ↓
6. Formatted error response
```

### Error Types
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (auth required)
- **403**: Forbidden (permission denied)
- **404**: Not Found (resource missing)
- **500**: Internal Server Error (unexpected errors)

## Testing Strategy

### Unit Tests
- Test individual functions
- Mock external dependencies
- Fast execution

### Integration Tests
- Test layer interactions
- Use test database
- Real external calls (where appropriate)

### End-to-End Tests
- Test full user workflows
- API requests → database
- Verify business logic

## Deployment

### Environment Setup
1. Production environment variables
2. Database migrations
3. Storage configuration
4. Secret management

### Recommended Stack
- **Server**: AWS EC2, Google Cloud Run, or similar
- **Database**: Supabase (managed PostgreSQL)
- **Storage**: Supabase Storage
- **Reverse Proxy**: Nginx
- **Process Manager**: Gunicorn + Uvicorn workers

### CI/CD
1. Code push to repository
2. Run tests
3. Build Docker image
4. Deploy to staging
5. Run smoke tests
6. Deploy to production

## Maintenance

### Code Organization
- Keep layers separated
- Follow existing patterns
- Document new features
- Write tests

### Database Migrations
- Use migration scripts
- Test in staging first
- Backup before running
- Version control migrations

### Monitoring
- Check logs regularly
- Monitor error rates
- Track API performance
- Review user feedback

## Future Enhancements

### Planned Features
- WebSocket support for real-time updates
- Recipe versioning
- Advanced filtering
- Meal planning
- Grocery lists
- Unit conversions

### Architecture Evolution
- Microservices (if needed)
- Event-driven architecture
- GraphQL API option
- Real-time collaboration
