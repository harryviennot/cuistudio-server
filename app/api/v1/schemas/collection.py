"""
Collection API schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============= Request Schemas =============

class CollectionCreateRequest(BaseModel):
    """Create collection request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CollectionUpdateRequest(BaseModel):
    """Update collection request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    sort_order: Optional[int] = None


class AddRecipeToCollectionRequest(BaseModel):
    """Add recipe to collection request"""
    recipe_id: str


class SaveRecipeRequest(BaseModel):
    """
    Save a recipe to a collection.

    Used for:
    - Publishing draft recipes after extraction preview
    - Adding existing recipes to user's collection
    """
    recipe_id: str = Field(..., description="Recipe ID to save")
    collection_id: Optional[str] = Field(
        None,
        description="Collection ID to save to. If not provided, uses default collection based on context."
    )


# ============= Response Schemas =============

class CollectionResponse(BaseModel):
    """Collection response"""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    is_system: bool
    sort_order: int
    recipe_count: int = 0
    created_at: datetime
    updated_at: datetime


class CollectionListResponse(BaseModel):
    """List of collections"""
    collections: List[CollectionResponse]


class CollectionRecipeResponse(BaseModel):
    """Recipe in a collection"""
    id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source_type: str
    is_public: bool
    added_at: datetime
    created_at: datetime


class CollectionWithRecipesResponse(BaseModel):
    """Collection with its recipes"""
    collection: CollectionResponse
    recipes: List[CollectionRecipeResponse]
    total_count: int


class SaveRecipeResponse(BaseModel):
    """Response from saving a recipe"""
    recipe_id: str
    collection_id: str
    added_to_collection: bool
    was_draft: bool = Field(
        False,
        description="True if the recipe was a draft that got published"
    )
