"""
Collection API schemas

Virtual collections system:
- "extracted" = user_recipe_data WHERE was_extracted = true
- "saved" = user_recipe_data WHERE is_favorite = true
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.domain.models import RecipeTimings


# ============= Request Schemas =============

class SaveRecipeRequest(BaseModel):
    """
    Save/publish a recipe.

    Used for publishing draft recipes after extraction preview.
    The collection_id field is deprecated and ignored - recipes are
    automatically added to the virtual "extracted" collection.
    """
    recipe_id: str = Field(..., description="Recipe ID to save/publish")
    collection_id: Optional[str] = Field(
        None,
        description="DEPRECATED: Collection ID is ignored. Recipes are automatically in 'extracted'.",
        deprecated=True
    )
    is_public: Optional[bool] = Field(
        None,
        description="Whether the recipe should be publicly visible. If not provided, defaults to True."
    )


# ============= Response Schemas =============

class CollectionResponse(BaseModel):
    """
    Virtual collection response.

    Collections are now computed on-the-fly from user_recipe_data.
    The id field contains the slug for virtual collections.
    """
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    is_system: bool
    sort_order: int
    recipe_count: int = 0
    created_at: Optional[datetime] = None  # Optional for virtual collections
    updated_at: Optional[datetime] = None  # Optional for virtual collections


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
    timings: Optional[RecipeTimings] = None


class CollectionWithRecipesResponse(BaseModel):
    """Collection with its recipes"""
    collection: CollectionResponse
    recipes: List[CollectionRecipeResponse]
    total_count: int


class SaveRecipeResponse(BaseModel):
    """Response from saving a recipe"""
    recipe_id: str
    collection_id: Optional[str] = Field(
        None,
        description="DEPRECATED: Always None in new system. Recipes are in virtual collections."
    )
    added_to_collection: bool
    was_draft: bool = Field(
        False,
        description="True if the recipe was a draft that got published"
    )


class CollectionCountsResponse(BaseModel):
    """Recipe counts for system collections"""
    extracted: int = Field(..., description="Count of recipes in the 'extracted' virtual collection")
    saved: int = Field(..., description="Count of recipes in the 'saved' virtual collection")
