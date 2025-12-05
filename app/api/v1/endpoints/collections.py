"""
Collections endpoints

Virtual collections system:
- "extracted" = user_recipe_data WHERE was_extracted = true
- "saved" = user_recipe_data WHERE is_favorite = true

These are virtual collections computed on-the-fly from user_recipe_data.
No more user_collections or collection_recipes tables.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
import logging

from app.core.database import get_supabase_admin_client
from app.core.security import get_current_user
from app.repositories.user_recipe_repository import UserRecipeRepository
from app.api.v1.schemas.collection import (
    CollectionResponse,
    CollectionWithRecipesResponse,
    CollectionRecipeResponse,
    CollectionCountsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collections", tags=["Collections"])


# Virtual collection metadata (no database lookup needed)
VIRTUAL_COLLECTIONS = {
    "extracted": {
        "id": "extracted",
        "name": "All Recipes",
        "slug": "extracted",
        "description": "All recipes you've extracted",
        "is_system": True,
        "sort_order": 0,
    },
    "saved": {
        "id": "saved",
        "name": "Favorites",
        "slug": "saved",
        "description": "Your favorite recipes",
        "is_system": True,
        "sort_order": 1,
    }
}


@router.get("/counts", response_model=CollectionCountsResponse)
async def get_collection_counts(
    current_user: dict = Depends(get_current_user),
    admin_supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Get recipe counts for system collections.

    Returns counts for 'extracted' (All Recipes) and 'saved' (Favorites) collections.
    This is a lightweight endpoint for updating UI without fetching full collection data.
    """
    try:
        user_recipe_repo = UserRecipeRepository(admin_supabase)

        # Count extracted recipes (was_extracted = true)
        extracted_count = await user_recipe_repo.count_user_extracted_recipes(
            current_user["id"]
        )

        # Count favorite recipes (is_favorite = true)
        saved_count = await user_recipe_repo.count_user_favorites(
            current_user["id"]
        )

        return CollectionCountsResponse(
            extracted=extracted_count,
            saved=saved_count
        )

    except Exception as e:
        logger.error(f"Error getting collection counts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection counts: {str(e)}"
        )


@router.get("/by-slug/{slug}", response_model=CollectionWithRecipesResponse)
async def get_collection_by_slug(
    slug: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    admin_supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Get a virtual collection by slug with its recipes.

    Supported slugs:
    - 'extracted': All recipes the user has extracted
    - 'saved': All recipes the user has favorited
    """
    try:
        # Validate slug
        if slug not in VIRTUAL_COLLECTIONS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection '{slug}' not found"
            )

        user_recipe_repo = UserRecipeRepository(admin_supabase)
        collection_meta = VIRTUAL_COLLECTIONS[slug]

        if slug == "extracted":
            # Get extracted recipes
            records = await user_recipe_repo.get_user_extracted_recipes(
                user_id=current_user["id"],
                limit=limit,
                offset=offset
            )
            total_count = await user_recipe_repo.count_user_extracted_recipes(
                current_user["id"]
            )
        else:  # saved
            # Get favorite recipes
            records = await user_recipe_repo.get_user_favorites(
                user_id=current_user["id"],
                limit=limit,
                offset=offset
            )
            total_count = await user_recipe_repo.count_user_favorites(
                current_user["id"]
            )

        # Transform records to response format
        recipe_responses = []
        for record in records:
            recipe = record.get("recipes", {})
            if recipe:
                recipe_responses.append(
                    CollectionRecipeResponse(
                        id=recipe["id"],
                        title=recipe["title"],
                        description=recipe.get("description"),
                        image_url=recipe.get("image_url"),
                        servings=recipe.get("servings"),
                        difficulty=recipe.get("difficulty"),
                        tags=recipe.get("tags", []),
                        source_type=recipe["source_type"],
                        is_public=recipe["is_public"],
                        added_at=record.get("created_at", recipe["created_at"]),
                        created_at=recipe["created_at"]
                    )
                )

        return CollectionWithRecipesResponse(
            collection=CollectionResponse(
                id=collection_meta["id"],
                name=collection_meta["name"],
                slug=collection_meta["slug"],
                description=collection_meta["description"],
                is_system=collection_meta["is_system"],
                sort_order=collection_meta["sort_order"],
                recipe_count=total_count,
                created_at=None,  # Virtual collection has no created_at
                updated_at=None
            ),
            recipes=recipe_responses,
            total_count=total_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection by slug: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection: {str(e)}"
        )
