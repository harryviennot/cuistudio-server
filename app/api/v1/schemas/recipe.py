"""
Recipe API schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.domain.models import Ingredient, Instruction, RecipeTimings
from app.domain.enums import SourceType, DifficultyLevel


# ============= Request Schemas =============

class RecipeCreateRequest(BaseModel):
    """Create recipe request"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None

    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[Instruction] = Field(default_factory=list)

    servings: Optional[int] = Field(None, ge=1)
    difficulty: Optional[DifficultyLevel] = None
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)

    timings: Optional[RecipeTimings] = None

    source_type: SourceType
    source_url: Optional[str] = None

    is_public: bool = True


class RecipeUpdateRequest(BaseModel):
    """Update recipe request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None

    ingredients: Optional[List[Ingredient]] = None
    instructions: Optional[List[Instruction]] = None

    servings: Optional[int] = Field(None, ge=1)
    difficulty: Optional[DifficultyLevel] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None

    timings: Optional[RecipeTimings] = None

    is_public: Optional[bool] = None


class RecipeForkRequest(BaseModel):
    """Fork recipe request"""
    title: Optional[str] = None  # Override title if desired
    is_public: Optional[bool] = None  # Override privacy


class RecipeRatingRequest(BaseModel):
    """Rate recipe request (supports half-stars: 0.5, 1.0, 1.5, ..., 5.0)"""
    rating: float = Field(..., ge=0.5, le=5.0)


class RecipeTimingsUpdateRequest(BaseModel):
    """Update recipe timings request"""
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)


class UserRecipeDataUpdate(BaseModel):
    """Update user-specific recipe data"""
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    custom_prep_time_minutes: Optional[int] = None
    custom_cook_time_minutes: Optional[int] = None
    custom_difficulty: Optional[DifficultyLevel] = None
    notes: Optional[str] = None
    custom_servings: Optional[int] = None
    is_favorite: Optional[bool] = None


class RecipeSearchRequest(BaseModel):
    """Natural language search request"""
    query: str = Field(..., min_length=1)
    limit: int = Field(20, ge=1, le=100)


# ============= Response Schemas =============

class RecipeContributorResponse(BaseModel):
    """Recipe contributor info"""
    user_id: str
    user_email: Optional[str] = None
    contribution_type: str
    order: int


class RecipeResponse(BaseModel):
    """Recipe response"""
    id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None

    ingredients: List[Ingredient]
    instructions: List[Instruction]

    servings: Optional[int] = None
    difficulty: Optional[DifficultyLevel] = None
    tags: List[str]
    categories: List[str]

    timings: Optional[RecipeTimings] = None

    source_type: SourceType
    source_url: Optional[str] = None

    created_by: str
    original_recipe_id: Optional[str] = None
    fork_count: int

    # Rating aggregation (half-star support)
    average_rating: Optional[float] = None
    rating_count: int = 0
    rating_distribution: Optional[dict] = None

    # Cooking count aggregation
    total_times_cooked: int = 0

    is_public: bool

    # Additional info
    contributors: List[RecipeContributorResponse] = Field(default_factory=list)
    user_data: Optional['UserRecipeDataResponse'] = None  # If user is authenticated

    # Video source info (only for video-extracted recipes)
    video_platform: Optional[str] = None  # tiktok, youtube, instagram

    created_at: datetime
    updated_at: datetime


class UserRecipeDataResponse(BaseModel):
    """User-specific recipe data response"""
    rating: Optional[float] = None
    custom_prep_time_minutes: Optional[int] = None
    custom_cook_time_minutes: Optional[int] = None
    custom_difficulty: Optional[DifficultyLevel] = None
    notes: Optional[str] = None
    custom_servings: Optional[int] = None
    times_cooked: int
    last_cooked_at: Optional[datetime] = None
    is_favorite: bool


class RecipeListItemResponse(BaseModel):
    """Simplified recipe for list views"""
    id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None

    servings: Optional[int] = None
    difficulty: Optional[DifficultyLevel] = None
    tags: List[str]
    categories: List[str]

    timings: Optional[RecipeTimings] = None

    created_by: str
    is_public: bool
    fork_count: int

    # Rating aggregation
    average_rating: Optional[float] = None
    rating_count: int = 0

    # Cooking count aggregation
    total_times_cooked: int = 0

    # User data if authenticated
    user_rating: Optional[float] = None
    is_favorite: bool = False

    # Video source info (only for video-extracted recipes)
    video_platform: Optional[str] = None  # tiktok, youtube, instagram

    created_at: datetime


class RecipeTimingsUpdateResponse(BaseModel):
    """Response for timing update"""
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    total_time_minutes: Optional[int] = None
    updated_base_recipe: bool  # True if base recipe was updated, False if user customization


class RecipeRatingUpdateResponse(BaseModel):
    """Response for rating update"""
    user_rating: float
    previous_user_rating: Optional[float] = None
    recipe_average_rating: Optional[float] = None
    recipe_rating_count: int
    recipe_rating_distribution: Optional[dict] = None


class CookingStatsResponse(BaseModel):
    """Cooking statistics for a recipe in a time window"""
    cook_count: int
    unique_users: int
    time_window_days: int


class TrendingRecipeResponse(RecipeResponse):
    """Trending recipe with cooking statistics"""
    cooking_stats: CookingStatsResponse


class UserCookingHistoryItemResponse(BaseModel):
    """User's cooking history for a single cooking event"""
    # Event identification
    event_id: str
    recipe_id: str
    recipe_title: str

    # Recipe info (for display)
    recipe_image_url: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None

    # Per-event data
    rating: Optional[float] = None  # Rating given at THIS cooking session
    cooking_image_url: Optional[str] = None  # Photo from THIS cooking session
    duration_minutes: Optional[int] = None  # Actual cooking time for this session
    cooked_at: datetime

    # Aggregates
    times_cooked: int  # Total times user has cooked this recipe


class MarkRecipeAseCookedRequest(BaseModel):
    """Request to mark a recipe as cooked with optional session data"""
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    image_url: Optional[str] = None  # URL of uploaded cooking photo
    duration_minutes: Optional[int] = Field(None, ge=0)


class UpdateCookingEventRequest(BaseModel):
    """Request to update an existing cooking event"""
    cooked_at: Optional[datetime] = None
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    image_url: Optional[str] = None  # Set to explicit null to remove image


class CookingEventResponse(BaseModel):
    """Response for a single cooking event after update"""
    event_id: str
    recipe_id: str
    cooked_at: datetime
    rating: Optional[float] = None
    cooking_image_url: Optional[str] = None
    duration_minutes: Optional[int] = None
