"""
Discovery endpoints for recipe discovery and trending features.

This module handles all discovery-related endpoints:
- Trending recipes (most cooked)
- Most extracted recipes (from video/website sources)
- Highest rated recipes
- Recently added public recipes
- User cooking history
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from supabase import Client
from typing import List, Dict, Any, Optional
import logging

from app.core.database import get_supabase_client, get_supabase_user_client
from app.core.security import get_current_user, get_current_user_optional
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.user_recipe_repository import UserRecipeRepository
from app.domain.models import RecipeTimings, Ingredient, Instruction
from app.api.v1.schemas.recipe import (
    TrendingRecipeResponse,
    UserCookingHistoryItemResponse,
    UserRecipeDataResponse,
    RecipeCategoryResponse,
)
from app.api.v1.schemas.discovery import (
    MostExtractedRecipeResponse,
    HighestRatedRecipeResponse,
    RecentRecipeResponse,
    SourceCategory,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discovery", tags=["Discovery"])


def _transform_recipe_for_response(
    recipe: Dict[str, Any],
    user_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Transform raw database recipe data to match RecipeResponse schema.

    This converts individual timing columns into a timings object,
    ensures ingredients/instructions are properly formatted,
    and attaches user-specific data if available.

    Args:
        recipe: Raw recipe data from database
        user_data: Optional user-specific data (is_favorite, rating, etc.)
    """
    # Build timings object from individual columns
    # For discovery endpoints, use prep + cook time only (exclude resting time)
    # This prevents long resting times (e.g., marinating, fermentation) from
    # discouraging users on the home page where the time isn't explained
    if recipe.get("prep_time_minutes") or recipe.get("cook_time_minutes") or recipe.get("total_time_minutes"):
        prep = recipe.get("prep_time_minutes") or 0
        cook = recipe.get("cook_time_minutes") or 0
        active_time = prep + cook if (prep or cook) else recipe.get("total_time_minutes")

        recipe["timings"] = RecipeTimings(
            prep_time_minutes=recipe.get("prep_time_minutes"),
            cook_time_minutes=recipe.get("cook_time_minutes"),
            total_time_minutes=active_time
        )
    else:
        recipe["timings"] = None

    # Ensure ingredients are properly formatted
    if recipe.get("ingredients"):
        recipe["ingredients"] = [
            Ingredient(**ing) if isinstance(ing, dict) else ing
            for ing in recipe["ingredients"]
        ]
    else:
        recipe["ingredients"] = []

    # Ensure instructions are properly formatted
    if recipe.get("instructions"):
        recipe["instructions"] = [
            Instruction(**inst) if isinstance(inst, dict) else inst
            for inst in recipe["instructions"]
        ]
    else:
        recipe["instructions"] = []

    # Ensure contributors is a list (even if empty)
    if not recipe.get("contributors"):
        recipe["contributors"] = []

    # Handle category data (enriched by enrich_with_category)
    if recipe.get("category"):
        cat = recipe["category"]
        recipe["category"] = RecipeCategoryResponse(
            id=cat["id"],
            slug=cat["slug"]
        )
    else:
        recipe["category"] = None

    # Attach user-specific data if available
    if user_data:
        recipe["user_data"] = UserRecipeDataResponse(
            is_favorite=user_data.get("is_favorite", False),
            rating=user_data.get("rating"),
            times_cooked=user_data.get("times_cooked", 0),
            custom_prep_time_minutes=user_data.get("custom_prep_time_minutes"),
            custom_cook_time_minutes=user_data.get("custom_cook_time_minutes"),
            custom_difficulty=user_data.get("custom_difficulty"),
            notes=user_data.get("notes"),
            custom_servings=user_data.get("custom_servings"),
            last_cooked_at=user_data.get("last_cooked_at"),
        )
    else:
        recipe["user_data"] = None

    return recipe


async def _get_user_data_map(
    user_id: Optional[str],
    recipe_ids: List[str],
    request: Request
) -> Dict[str, Dict[str, Any]]:
    """
    Batch fetch user data for a list of recipes.

    Returns a dict mapping recipe_id -> user_data.
    Returns empty dict if user is not authenticated or no recipes.

    Uses the user's JWT to create a Supabase client that respects RLS policies.
    """
    if not user_id or not recipe_ids:
        return {}

    # Use user client with their JWT so RLS policies work correctly
    user_client = get_supabase_user_client(request)
    user_repo = UserRecipeRepository(user_client)
    return await user_repo.get_user_data_for_recipes(user_id, recipe_ids)


@router.get("/trending", response_model=List[TrendingRecipeResponse])
async def get_trending_recipes(
    request: Request,
    time_window_days: int = Query(7, ge=1, le=365, description="Number of days to look back (default: 7 for 'this week')"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get trending recipes based on cooking frequency in a time window.

    This endpoint returns recipes ordered by how many times they've been cooked
    in the specified time window. Great for discovering popular recipes!

    Examples:
    - time_window_days=7: Most cooked recipes this week
    - time_window_days=30: Most cooked recipes this month
    - time_window_days=1: Trending today

    Returns recipes with cooking statistics including:
    - cook_count: Number of times cooked in the time window
    - unique_users: Number of unique users who cooked it

    If authenticated, also includes user-specific data (is_favorite, rating, etc.)
    """
    try:
        repo = RecipeRepository(supabase)
        trending_recipes = await repo.get_trending_recipes(
            time_window_days=time_window_days,
            limit=limit,
            offset=offset
        )

        # Batch enrich categories (avoids N+1 queries)
        trending_recipes = await repo.enrich_with_category(trending_recipes)

        # Batch fetch user data if authenticated
        user_id = current_user["id"] if current_user else None
        recipe_ids = [r["id"] for r in trending_recipes]
        user_data_map = await _get_user_data_map(user_id, recipe_ids, request)

        # Transform each recipe to match the response schema
        return [
            _transform_recipe_for_response(recipe, user_data_map.get(recipe["id"]))
            for recipe in trending_recipes
        ]
    except Exception as e:
        logger.error(f"Error fetching trending recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending recipes")


@router.get("/cooking-history", response_model=List[UserCookingHistoryItemResponse])
async def get_cooking_history(
    time_window_days: int = Query(365, ge=1, le=365, description="Number of days to look back (default: 365)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get the current user's cooking history as individual cooking events.

    Returns each cooking session with:
    - event_id: Unique identifier for this cooking event
    - recipe_id, recipe_title: The recipe that was cooked
    - recipe_image_url: The recipe's main image
    - difficulty: Recipe difficulty level
    - rating: The rating given at this specific cooking session (may differ from current rating)
    - cooking_image_url: Photo taken during this cooking session (signed URL, expires in 1 hour)
    - duration_minutes: Actual cooking time for this session
    - cooked_at: When this cooking session occurred
    - times_cooked: Total times the user has cooked this recipe

    Note: cooking_image_url is a signed URL that expires after 1 hour for privacy.
    The mobile app should refresh the cooking history if images fail to load after extended viewing.
    """
    from app.services.upload_service import UploadService

    try:
        repo = RecipeRepository(supabase)
        upload_service = UploadService(supabase)

        cooking_history = await repo.get_user_cooking_history(
            user_id=current_user["id"],
            time_window_days=time_window_days,
            limit=limit,
            offset=offset
        )

        # Generate signed URLs for cooking photos (private bucket)
        for event in cooking_history:
            if event.get("cooking_image_url"):
                stored_url = event["cooking_image_url"]
                # Extract path from stored URL
                path = UploadService.extract_storage_path(stored_url, "cooking-events")

                if path:
                    # Generate fresh signed URL
                    signed_url = upload_service.create_signed_url(
                        bucket="cooking-events",
                        path=path,
                        expires_in=3600  # 1 hour
                    )
                    if signed_url:
                        event["cooking_image_url"] = signed_url
                    else:
                        # If signed URL generation fails, clear the URL
                        # rather than returning an inaccessible public URL
                        logger.warning(f"Failed to generate signed URL for cooking photo: {path}")
                        event["cooking_image_url"] = None

        return cooking_history
    except Exception as e:
        logger.error(f"Error fetching cooking history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch cooking history")


@router.get("/most-extracted", response_model=List[MostExtractedRecipeResponse])
async def get_most_extracted_recipes(
    request: Request,
    source_category: SourceCategory = Query(..., description="Filter by source: 'video' for social media, 'website' for recipe sites"),
    limit: int = Query(8, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get most extracted recipes by source category.

    This endpoint returns public recipes ordered by how many users have extracted them.
    Great for discovering what's trending on social media or popular recipe websites!

    Source categories:
    - video: Recipes extracted from TikTok, Instagram, YouTube (Trending on Socials)
    - website: Recipes extracted from recipe websites/URLs (Popular Recipes Online)

    Returns recipes with extraction statistics including:
    - extraction_count: Number of times this recipe was extracted
    - unique_extractors: Number of unique users who extracted it

    If authenticated, also includes user-specific data (is_favorite, rating, etc.)
    """
    try:
        repo = RecipeRepository(supabase)
        extracted_recipes = await repo.get_most_extracted_recipes(
            source_category=source_category.value,
            limit=limit,
            offset=offset
        )

        # Batch enrich categories (avoids N+1 queries)
        extracted_recipes = await repo.enrich_with_category(extracted_recipes)

        # Batch fetch user data if authenticated
        user_id = current_user["id"] if current_user else None
        recipe_ids = [r["id"] for r in extracted_recipes]
        user_data_map = await _get_user_data_map(user_id, recipe_ids, request)

        # Transform each recipe to match the response schema
        return [
            _transform_recipe_for_response(recipe, user_data_map.get(recipe["id"]))
            for recipe in extracted_recipes
        ]
    except Exception as e:
        logger.error(f"Error fetching most extracted recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch most extracted recipes")


@router.get("/highest-rated", response_model=List[HighestRatedRecipeResponse])
async def get_highest_rated_recipes(
    request: Request,
    min_rating_count: int = Query(3, ge=1, le=100, description="Minimum number of ratings required"),
    limit: int = Query(8, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get highest rated public recipes.

    Returns public recipes ordered by average rating, filtered by minimum rating count
    to ensure quality and prevent recipes with a single 5-star rating from dominating.

    Returns recipes with rating statistics including:
    - average_rating: The recipe's average rating (0.5-5.0)
    - rating_count: Number of ratings received

    If authenticated, also includes user-specific data (is_favorite, rating, etc.)
    """
    try:
        repo = RecipeRepository(supabase)
        rated_recipes = await repo.get_highest_rated_recipes(
            min_rating_count=min_rating_count,
            limit=limit,
            offset=offset
        )

        # Batch enrich categories (avoids N+1 queries)
        rated_recipes = await repo.enrich_with_category(rated_recipes)

        # Batch fetch user data if authenticated
        user_id = current_user["id"] if current_user else None
        recipe_ids = [r["id"] for r in rated_recipes]
        user_data_map = await _get_user_data_map(user_id, recipe_ids, request)

        # Transform each recipe to match the response schema
        return [
            _transform_recipe_for_response(recipe, user_data_map.get(recipe["id"]))
            for recipe in rated_recipes
        ]
    except Exception as e:
        logger.error(f"Error fetching highest rated recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch highest rated recipes")


@router.get("/recent", response_model=List[RecentRecipeResponse])
async def get_recent_recipes(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get recently added public recipes.

    Returns public recipes ordered by creation date (newest first).
    Supports infinite pagination for the home page masonry grid.

    If authenticated, also includes user-specific data (is_favorite, rating, etc.)
    """
    try:
        repo = RecipeRepository(supabase)
        recent_recipes = await repo.get_recent_public_recipes(
            limit=limit,
            offset=offset
        )

        # Batch enrich categories (avoids N+1 queries)
        recent_recipes = await repo.enrich_with_category(recent_recipes)

        # Batch fetch user data if authenticated
        user_id = current_user["id"] if current_user else None
        recipe_ids = [r["id"] for r in recent_recipes]
        user_data_map = await _get_user_data_map(user_id, recipe_ids, request)

        # Transform each recipe to match the response schema
        return [
            _transform_recipe_for_response(recipe, user_data_map.get(recipe["id"]))
            for recipe in recent_recipes
        ]
    except Exception as e:
        logger.error(f"Error fetching recent recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent recipes")


@router.get("/popular", response_model=List[RecentRecipeResponse])
async def get_popular_recipes(
    request: Request,
    category_id: Optional[str] = Query(None, description="Filter by category UUID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get popular public recipes, optionally filtered by category.

    Recipes are sorted by a popularity score that combines rating quality with engagement:
    - popularity_score = (average_rating * rating_count) + total_times_cooked

    This balances highly-rated recipes with frequently-cooked recipes.

    Query parameters:
    - category_id: Optional UUID to filter recipes by category
    - limit: Maximum results per page (default: 20)
    - offset: Pagination offset (default: 0)

    If authenticated, also includes user-specific data (is_favorite, rating, etc.)
    """
    try:
        repo = RecipeRepository(supabase)
        popular_recipes = await repo.get_popular_recipes(
            category_id=category_id,
            limit=limit,
            offset=offset
        )

        # Batch fetch user data if authenticated
        user_id = current_user["id"] if current_user else None
        recipe_ids = [r["id"] for r in popular_recipes]
        user_data_map = await _get_user_data_map(user_id, recipe_ids, request)

        # Transform each recipe to match the response schema
        return [
            _transform_recipe_for_response(recipe, user_data_map.get(recipe["id"]))
            for recipe in popular_recipes
        ]
    except Exception as e:
        logger.error(f"Error fetching popular recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch popular recipes")
