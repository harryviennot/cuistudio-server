"""
Category endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List
import logging

from app.core.database import get_supabase_client
from app.repositories.category_repository import CategoryRepository
from app.repositories.recipe_repository import RecipeRepository
from app.api.v1.schemas.category import (
    CategoryResponse,
    CategoryWithCountResponse,
)
from app.api.v1.schemas.recipe import RecipeListItemResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    include_counts: bool = Query(False, description="Include recipe counts per category"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get all categories.

    Categories are ordered by display_order.
    Frontend handles translation via i18n using the slug as the key.
    """
    try:
        repo = CategoryRepository(supabase)

        if include_counts:
            categories = await repo.get_recipe_count_by_category()
            return [CategoryWithCountResponse(**cat) for cat in categories]
        else:
            categories = await repo.get_all()
            return [CategoryResponse(**cat) for cat in categories]

    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories"
        )


@router.get("/{slug}", response_model=CategoryResponse)
async def get_category(
    slug: str,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get a single category by slug.

    Frontend handles translation via i18n using the slug.
    """
    try:
        repo = CategoryRepository(supabase)

        category = await repo.get_by_slug(slug)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{slug}' not found"
            )

        return CategoryResponse(**category)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching category {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch category"
        )


@router.get("/{slug}/recipes", response_model=List[RecipeListItemResponse])
async def get_recipes_by_category(
    slug: str,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get public recipes in a specific category.

    Paginated results, ordered by creation date (newest first).
    """
    try:
        cat_repo = CategoryRepository(supabase)
        recipe_repo = RecipeRepository(supabase)

        # Get category ID
        category = await cat_repo.get_by_slug(slug)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{slug}' not found"
            )

        # Get recipes in this category
        recipes = await recipe_repo.get_public_recipes(
            filters={"category_id": category["id"]},
            limit=limit,
            offset=offset
        )

        return [RecipeListItemResponse(**recipe) for recipe in recipes]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recipes for category {slug}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recipes"
        )
