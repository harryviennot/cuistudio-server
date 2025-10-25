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
    """Rate recipe request"""
    rating: int = Field(..., ge=1, le=5)


class UserRecipeDataUpdate(BaseModel):
    """Update user-specific recipe data"""
    rating: Optional[int] = Field(None, ge=1, le=5)
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

    is_public: bool

    # Additional info
    contributors: List[RecipeContributorResponse] = Field(default_factory=list)
    user_data: Optional['UserRecipeDataResponse'] = None  # If user is authenticated

    created_at: datetime
    updated_at: datetime


class UserRecipeDataResponse(BaseModel):
    """User-specific recipe data response"""
    rating: Optional[int] = None
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

    # User data if authenticated
    user_rating: Optional[int] = None
    is_favorite: bool = False

    created_at: datetime
