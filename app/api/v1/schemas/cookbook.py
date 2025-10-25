"""
Cookbook API schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING, Any
from datetime import datetime

if TYPE_CHECKING:
    from app.api.v1.schemas.recipe import RecipeListItemResponse


# ============= Request Schemas =============

class CookbookCreateRequest(BaseModel):
    """Create cookbook request"""
    title: str = Field(..., min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_public: bool = False


class CookbookUpdateRequest(BaseModel):
    """Update cookbook request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_public: Optional[bool] = None


class CookbookAddRecipeRequest(BaseModel):
    """Add recipe to cookbook"""
    recipe_id: str
    folder_id: Optional[str] = None  # If adding to a specific folder


class FolderCreateRequest(BaseModel):
    """Create folder in cookbook"""
    name: str = Field(..., min_length=1, max_length=100)
    parent_folder_id: Optional[str] = None  # For nested folders


class FolderUpdateRequest(BaseModel):
    """Update folder"""
    name: str = Field(..., min_length=1, max_length=100)


# ============= Response Schemas =============

class CookbookResponse(BaseModel):
    """Cookbook response"""
    id: str
    user_id: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_public: bool
    recipe_count: int
    created_at: datetime
    updated_at: datetime


class FolderResponse(BaseModel):
    """Folder response"""
    id: str
    cookbook_id: str
    parent_folder_id: Optional[str] = None
    name: str
    order: int
    created_at: datetime


class CookbookDetailResponse(CookbookResponse):
    """Detailed cookbook with folders and recipes"""
    folders: List[FolderResponse] = Field(default_factory=list)
    recipes: List[Any] = Field(default_factory=list)  # List of RecipeListItemResponse
