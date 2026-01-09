"""
Category API schemas
"""
from pydantic import BaseModel
from typing import List, Optional


class CategoryResponse(BaseModel):
    """
    Category response.

    Frontend handles translation via i18n files using the slug as the key.
    """
    id: str
    slug: str
    icon: Optional[str] = None
    display_order: int

    class Config:
        from_attributes = True


class CategoryWithCountResponse(CategoryResponse):
    """Category with recipe count for browse pages"""
    recipe_count: int = 0


class CategoryListResponse(BaseModel):
    """List of categories"""
    categories: List[CategoryResponse]
    total: int
