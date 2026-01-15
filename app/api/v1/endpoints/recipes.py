"""
Recipe endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from supabase import Client
from typing import List, Optional, Dict, Any
import logging

from app.core.database import get_supabase_client, get_supabase_admin_client
from app.core.security import get_current_user, get_current_user_optional, get_authenticated_user
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.user_recipe_repository import UserRecipeRepository
from app.services.openai_service import OpenAIService
from app.api.v1.schemas.recipe import (
    RecipeCreateRequest,
    RecipeUpdateRequest,
    RecipeForkRequest,
    RecipeRatingRequest,
    RecipeTimingsUpdateRequest,
    RecipeTimingsUpdateResponse,
    UserRecipeDataUpdate,
    RecipeSearchRequest,
    RecipeResponse,
    RecipeListItemResponse,
    UserRecipeDataResponse,
    RecipeContributorResponse,
    RecipeCategoryResponse,
    MarkRecipeAseCookedRequest,
    UpdateCookingEventRequest,
    CookingEventResponse,
)
from app.repositories.category_repository import CategoryRepository
from app.api.v1.schemas.collection import (
    SaveRecipeRequest,
    SaveRecipeResponse
)
from app.api.v1.schemas.common import MessageResponse
from app.domain.models import RecipeTimings, Ingredient, Instruction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreateRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new recipe manually"""
    try:
        repo = RecipeRepository(supabase)
        cat_repo = CategoryRepository(supabase)

        # Resolve category_slug to category_id if provided
        category_id = None
        if recipe_data.category_slug:
            category_id = await cat_repo.get_id_by_slug(recipe_data.category_slug)

        # Prepare recipe data
        data = {
            "title": recipe_data.title,
            "description": recipe_data.description,
            "image_url": recipe_data.image_url,
            "ingredients": [ing.model_dump() for ing in recipe_data.ingredients],
            "instructions": [inst.model_dump() for inst in recipe_data.instructions],
            "servings": recipe_data.servings,
            "difficulty": recipe_data.difficulty.value if recipe_data.difficulty else None,
            "tags": recipe_data.tags,
            "category_id": category_id,
            "prep_time_minutes": recipe_data.timings.prep_time_minutes if recipe_data.timings else None,
            "cook_time_minutes": recipe_data.timings.cook_time_minutes if recipe_data.timings else None,
            "total_time_minutes": recipe_data.timings.total_time_minutes if recipe_data.timings else None,
            "source_type": recipe_data.source_type.value,
            "source_url": recipe_data.source_url,
            "created_by": current_user["id"],
            "is_public": recipe_data.is_public
        }

        recipe = await repo.create(data)

        # Create contributor record
        supabase.table("recipe_contributors").insert({
            "recipe_id": recipe["id"],
            "user_id": current_user["id"],
            "contribution_type": "creator",
            "order": 0
        }).execute()

        return await _format_recipe_response(recipe, current_user["id"], supabase)

    except Exception as e:
        logger.error(f"Error creating recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recipe: {str(e)}"
        )


@router.post("/save", response_model=SaveRecipeResponse, status_code=status.HTTP_201_CREATED)
async def save_recipe(
    save_request: SaveRecipeRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Save/publish a recipe.

    This endpoint is used after the user previews a recipe (from extraction)
    and decides to save it. It handles:
    - Publishing draft recipes (setting is_draft=false)
    - Marking recipe as extracted in user_recipe_data

    Flow:
    1. Submit extraction via POST /extraction/submit
    2. Poll job status via GET /extraction/jobs/{job_id} until completed
    3. Preview the draft recipe using GET /recipes/{recipe_id}
    4. Call this endpoint with recipe_id to publish and save

    Note: collection_id parameter is deprecated and ignored.
    Recipes are automatically added to the "extracted" virtual collection.
    """
    from app.services.recipe_save_service import RecipeSaveService

    try:
        save_service = RecipeSaveService(supabase)

        # Publish the draft and mark as extracted
        result = await save_service.publish_draft_recipe(
            user_id=current_user["id"],
            recipe_id=save_request.recipe_id,
            is_public=save_request.is_public
        )

        return SaveRecipeResponse(
            recipe_id=result["recipe_id"],
            collection_id=None,  # No collection ID in new system
            added_to_collection=True,  # Always added to virtual "extracted" collection
            was_draft=result.get("was_draft", False)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error saving recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save recipe: {str(e)}"
        )


@router.post("/{recipe_id}/favorite", response_model=SaveRecipeResponse)
async def favorite_recipe(
    recipe_id: str,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Add a recipe to the user's favorites.

    This sets is_favorite=true in user_recipe_data for this recipe.
    The recipe must be public or owned by the user.
    """
    from app.repositories.user_recipe_repository import UserRecipeRepository
    from app.repositories.recipe_repository import RecipeRepository

    try:
        recipe_repo = RecipeRepository(supabase)
        user_recipe_repo = UserRecipeRepository(supabase)

        # Verify recipe exists and is accessible
        recipe = await recipe_repo.get_by_id(recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )

        # Check if user can access this recipe (public or owned)
        if not recipe["is_public"] and recipe["created_by"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this recipe"
            )

        # Set favorite status
        await user_recipe_repo.set_favorite(
            user_id=current_user["id"],
            recipe_id=recipe_id,
            is_favorite=True
        )

        return SaveRecipeResponse(
            recipe_id=recipe_id,
            collection_id=None,  # No collection ID in new system
            added_to_collection=True,
            was_draft=False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error favoriting recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to favorite recipe: {str(e)}"
        )


@router.delete("/{recipe_id}/favorite", response_model=MessageResponse)
async def unfavorite_recipe(
    recipe_id: str,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Remove a recipe from the user's favorites.

    This sets is_favorite=false in user_recipe_data for this recipe.
    This does NOT delete the recipe.
    """
    from app.repositories.user_recipe_repository import UserRecipeRepository

    try:
        user_recipe_repo = UserRecipeRepository(supabase)

        # Set favorite status to false
        await user_recipe_repo.set_favorite(
            user_id=current_user["id"],
            recipe_id=recipe_id,
            is_favorite=False
        )

        return MessageResponse(message="Recipe removed from favorites")

    except Exception as e:
        logger.error(f"Error unfavoriting recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unfavorite recipe: {str(e)}"
        )


@router.get("/search", response_model=List[RecipeListItemResponse])
async def search_recipes_full_text(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    difficulty: Optional[str] = Query(None, regex="^(easy|medium|hard)$", description="Filter by difficulty level"),
    category_slugs: Optional[str] = Query(None, description="Filter by category slugs (comma-separated for OR logic)"),
    max_prep_time: Optional[int] = Query(None, ge=0, description="Maximum prep time in minutes"),
    max_cook_time: Optional[int] = Query(None, ge=0, description="Maximum cook time in minutes"),
    max_rest_time: Optional[int] = Query(None, ge=0, description="Maximum resting time in minutes"),
    min_time: Optional[int] = Query(None, ge=0, description="Minimum total cooking time in minutes (legacy)"),
    max_time: Optional[int] = Query(None, ge=0, description="Maximum total cooking time in minutes (legacy)"),
    sort_by: str = Query("relevance", regex="^(relevance|recent|rating|cook_count|time)$", description="Sort order"),
    library_only: bool = Query(False, description="Only return user's library recipes (favorites or extracted)"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Full-text search recipes with filters and sorting.

    Uses PostgreSQL full-text search with language-aware stemming and relevance ranking.

    Query Examples:
    - "chicken pasta" - finds recipes with chicken and pasta
    - "quick dinner" - finds quick dinner recipes
    - "grilled vegetables" - finds grilled veggie recipes (with stemming)

    Filters:
    - difficulty: Filter by "easy", "medium", or "hard"
    - category_slugs: Filter by categories (comma-separated, OR logic)
    - max_prep_time/max_cook_time/max_rest_time: Granular time filters (AND logic)
    - min_time/max_time: Filter by total cooking time range (legacy)
    - library_only: Only show user's saved/extracted recipes

    Sorting:
    - relevance: Sort by search relevance (default)
    - recent: Sort by creation date (newest first)
    - rating: Sort by average rating (highest first)
    - cook_count: Sort by popularity (most cooked first)
    - time: Sort by cooking time (quickest first)
    """
    try:
        from app.repositories.category_repository import CategoryRepository

        repo = RecipeRepository(supabase)
        user_id = current_user["id"] if current_user else None

        # Resolve category slugs to category_ids (supports multiple, comma-separated)
        category_ids = []
        if category_slugs:
            category_repo = CategoryRepository(supabase)
            for slug in category_slugs.split(","):
                slug = slug.strip()
                if slug:
                    category = await category_repo.get_by_slug(slug)
                    if category:
                        category_ids.append(category["id"])
                    else:
                        logger.warning(f"Category slug not found: {slug}")

        # Use filtered search with all parameters
        recipes = await repo.search_recipes_filtered(
            user_id=user_id,
            search_query=q,
            limit=limit,
            offset=offset,
            difficulty=difficulty,
            category_ids=category_ids if category_ids else None,
            max_prep_time=max_prep_time,
            max_cook_time=max_cook_time,
            max_rest_time=max_rest_time,
            min_time=min_time,
            max_time=max_time,
            sort_by=sort_by,
            library_only=library_only
        )

        # Batch enrich categories (avoids N+1 queries)
        recipes = await repo.enrich_with_category(recipes)

        # Batch fetch user data if authenticated
        user_data_map = {}
        if user_id and recipes:
            user_repo = UserRecipeRepository(supabase)
            recipe_ids = [r["id"] for r in recipes]
            user_data_map = await user_repo.get_user_data_for_recipes(user_id, recipe_ids)

        return [await _format_list_item_response(r, user_id, supabase, user_data_map.get(r["id"])) for r in recipes]

    except Exception as e:
        logger.error(f"Error searching recipes with full-text search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search recipes: {str(e)}"
        )


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a recipe by ID"""
    try:
        from app.core.database import get_supabase_user_client

        repo = RecipeRepository(supabase)
        recipe = await repo.get_with_contributors(recipe_id)

        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )

        # Check access permissions
        user_id = current_user["id"] if current_user else None

        if not recipe["is_public"]:
            if not user_id or recipe["created_by"] != user_id:
                # Check if shared with user
                if user_id:
                    share_check = await supabase.table("recipe_shares")\
                        .select("id")\
                        .eq("recipe_id", recipe_id)\
                        .eq("shared_with_user_id", user_id)\
                        .execute()

                    if not share_check.data:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this recipe"
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="This recipe is private"
                    )

        # Use user client with JWT token for RLS-aware operations
        user_client = get_supabase_user_client(request) if current_user else supabase
        return await _format_recipe_response(recipe, user_id, user_client)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recipe: {str(e)}"
        )


@router.get("", response_model=List[RecipeListItemResponse])
async def list_recipes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    difficulty: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated
    category_id: Optional[str] = None,  # Single category UUID
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """List public recipes with optional filters"""
    try:
        repo = RecipeRepository(supabase)

        filters = {}
        if difficulty:
            filters["difficulty"] = difficulty
        if tags:
            filters["tags"] = tags.split(",")
        if category_id:
            filters["category_id"] = category_id

        recipes = await repo.get_public_recipes(limit, offset, filters)

        # Batch enrich categories (avoids N+1 queries)
        recipes = await repo.enrich_with_category(recipes)

        user_id = current_user["id"] if current_user else None

        # Fetch user data for authenticated users (is_favorite, times_cooked, etc.)
        user_data_map = {}
        if user_id:
            user_repo = UserRecipeRepository(supabase)
            recipe_ids = [r["id"] for r in recipes]
            user_data_map = await user_repo.get_user_data_for_recipes(user_id, recipe_ids)

        return [await _format_list_item_response(r, user_id, supabase, user_data_map.get(r["id"])) for r in recipes]

    except Exception as e:
        logger.error(f"Error listing recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list recipes: {str(e)}"
        )


@router.get("/user/my-recipes", response_model=List[RecipeListItemResponse])
async def get_my_recipes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get current user's recipes"""
    try:
        repo = RecipeRepository(supabase)
        recipes = await repo.get_user_recipes(current_user["id"], limit, offset)

        # Batch enrich categories (avoids N+1 queries)
        recipes = await repo.enrich_with_category(recipes)

        # Batch fetch user data for all recipes in one query (eliminates N+1 problem)
        user_repo = UserRecipeRepository(supabase)
        recipe_ids = [r["id"] for r in recipes]
        user_data_map = await user_repo.get_user_data_for_recipes(current_user["id"], recipe_ids)

        return [await _format_list_item_response(r, current_user["id"], supabase, user_data_map.get(r["id"])) for r in recipes]

    except Exception as e:
        logger.error(f"Error getting user recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user recipes: {str(e)}"
        )


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: str,
    update_data: RecipeUpdateRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Update a recipe"""
    try:
        # Log the incoming request data
        logger.info(f"[UPDATE] Received update_data: {update_data.model_dump()}")
        logger.info(f"[UPDATE] category_slug field value: {update_data.category_slug!r}")

        repo = RecipeRepository(supabase)
        cat_repo = CategoryRepository(supabase)

        # Check ownership or collaboration permission
        recipe = await repo.get_by_id(recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )

        # Check if user owns recipe or has collaborate permission
        has_permission = recipe["created_by"] == current_user["id"]

        if not has_permission:
            share_check = await supabase.table("recipe_shares")\
                .select("permission_level")\
                .eq("recipe_id", recipe_id)\
                .eq("shared_with_user_id", current_user["id"])\
                .execute()

            if share_check.data and share_check.data[0]["permission_level"] == "collaborate":
                has_permission = True

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this recipe"
            )

        # Prepare update data
        data = {}
        if update_data.title is not None:
            data["title"] = update_data.title
        if update_data.description is not None:
            data["description"] = update_data.description
        if update_data.image_url is not None:
            data["image_url"] = update_data.image_url
        if update_data.ingredients is not None:
            data["ingredients"] = [ing.model_dump() for ing in update_data.ingredients]
        if update_data.instructions is not None:
            data["instructions"] = [inst.model_dump() for inst in update_data.instructions]
        if update_data.servings is not None:
            data["servings"] = update_data.servings
        if update_data.difficulty is not None:
            data["difficulty"] = update_data.difficulty.value
        if update_data.tags is not None:
            data["tags"] = update_data.tags
        # Handle category_slug -> category_id
        logger.info(f"[UPDATE] category_slug from request: {update_data.category_slug!r}")
        if update_data.category_slug is not None:
            category_id = await cat_repo.get_id_by_slug(update_data.category_slug)
            logger.info(f"[UPDATE] Resolved category_id: {category_id}")
            data["category_id"] = category_id
        if update_data.timings is not None:
            data["prep_time_minutes"] = update_data.timings.prep_time_minutes
            data["cook_time_minutes"] = update_data.timings.cook_time_minutes
            data["total_time_minutes"] = update_data.timings.total_time_minutes
        if update_data.is_public is not None:
            data["is_public"] = update_data.is_public

        logger.info(f"[UPDATE] Final data dict being sent to update: {list(data.keys())}")
        logger.info(f"[UPDATE] category_id in data: {'category_id' in data}, value: {data.get('category_id')}")
        updated_recipe = await repo.update(recipe_id, data)

        # If update didn't return data, fetch the recipe again
        if not updated_recipe:
            updated_recipe = await repo.get_by_id(recipe_id)
            if not updated_recipe:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve updated recipe"
                )

        return await _format_recipe_response(updated_recipe, current_user["id"], supabase)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update recipe: {str(e)}"
        )


@router.delete("/{recipe_id}", response_model=MessageResponse)
async def delete_recipe(
    recipe_id: str,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Delete a recipe (owner only, drafts can always be deleted)"""
    try:
        repo = RecipeRepository(supabase)

        # Check ownership
        recipe = await repo.get_by_id(recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )

        if recipe["created_by"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this recipe"
            )

        # Use admin client to bypass RLS for deletion
        deleted = await repo.delete(recipe_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete recipe"
            )

        return MessageResponse(message="Recipe deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete recipe: {str(e)}"
        )


@router.post("/{recipe_id}/fork", response_model=RecipeResponse)
async def fork_recipe(
    recipe_id: str,
    fork_data: RecipeForkRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Fork a recipe"""
    try:
        repo = RecipeRepository(supabase)

        # Get original recipe
        original = await repo.get_by_id(recipe_id)
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )

        # Check if user can access the recipe
        if not original["is_public"] and original["created_by"] != current_user["id"]:
            share_check = await supabase.table("recipe_shares")\
                .select("permission_level")\
                .eq("recipe_id", recipe_id)\
                .eq("shared_with_user_id", current_user["id"])\
                .execute()

            if not share_check.data or share_check.data[0]["permission_level"] not in ["fork", "collaborate"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to fork this recipe"
                )

        # Create forked recipe data
        forked_data = {
            "title": fork_data.title or f"{original['title']} (Fork)",
            "description": original["description"],
            "image_url": original["image_url"],
            "ingredients": original["ingredients"],
            "instructions": original["instructions"],
            "servings": original["servings"],
            "difficulty": original["difficulty"],
            "tags": original["tags"],
            "category_id": original.get("category_id"),
            "prep_time_minutes": original["prep_time_minutes"],
            "cook_time_minutes": original["cook_time_minutes"],
            "total_time_minutes": original["total_time_minutes"],
            "source_type": original["source_type"],
            "source_url": original["source_url"],
            "created_by": current_user["id"],
            "original_recipe_id": recipe_id,
            "is_public": fork_data.is_public if fork_data.is_public is not None else original["is_public"]
        }

        forked_recipe = await repo.fork_recipe(recipe_id, forked_data, current_user["id"])

        return await _format_recipe_response(forked_recipe, current_user["id"], supabase)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forking recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fork recipe: {str(e)}"
        )


@router.get("/{recipe_id}/forks", response_model=List[RecipeListItemResponse])
async def get_recipe_forks(
    recipe_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all forks of a recipe"""
    try:
        repo = RecipeRepository(supabase)
        forks = await repo.get_recipe_forks(recipe_id)

        # Batch enrich categories (avoids N+1 queries)
        forks = await repo.enrich_with_category(forks)

        user_id = current_user["id"] if current_user else None
        return [await _format_list_item_response(f, user_id, supabase) for f in forks]

    except Exception as e:
        logger.error(f"Error getting recipe forks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recipe forks: {str(e)}"
        )


@router.post("/{recipe_id}/user-data", response_model=UserRecipeDataResponse)
async def update_user_recipe_data(
    recipe_id: str,
    data: UserRecipeDataUpdate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update user-specific recipe data (rating, notes, etc.)"""
    try:
        repo = UserRecipeRepository(supabase)

        update_data = {}
        if data.rating is not None:
            update_data["rating"] = data.rating
        if data.custom_prep_time_minutes is not None:
            update_data["custom_prep_time_minutes"] = data.custom_prep_time_minutes
        if data.custom_cook_time_minutes is not None:
            update_data["custom_cook_time_minutes"] = data.custom_cook_time_minutes
        if data.custom_resting_time_minutes is not None:
            update_data["custom_resting_time_minutes"] = data.custom_resting_time_minutes
        if data.custom_difficulty is not None:
            update_data["custom_difficulty"] = data.custom_difficulty.value
        if data.notes is not None:
            update_data["notes"] = data.notes
        if data.custom_servings is not None:
            update_data["custom_servings"] = data.custom_servings
        if data.is_favorite is not None:
            update_data["is_favorite"] = data.is_favorite

        result = await repo.upsert_user_data(current_user["id"], recipe_id, update_data)

        return UserRecipeDataResponse(**result)

    except Exception as e:
        logger.error(f"Error updating user recipe data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user recipe data: {str(e)}"
        )


@router.post("/{recipe_id}/cooked", response_model=MessageResponse)
async def mark_recipe_cooked(
    recipe_id: str,
    request: Optional[MarkRecipeAseCookedRequest] = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Mark a recipe as cooked with optional session data.

    Creates a cooking event record with:
    - rating: Optional rating given at this cooking session (0.5-5.0)
    - image_url: Optional URL to a photo taken during cooking
    - duration_minutes: Optional actual cooking time in minutes

    If rating is provided, it also updates the user's current rating for the recipe.
    """
    try:
        repo = UserRecipeRepository(supabase)

        # Extract optional session data
        rating = request.rating if request else None
        image_url = request.image_url if request else None
        duration_minutes = request.duration_minutes if request else None

        await repo.increment_cooked_count(
            user_id=current_user["id"],
            recipe_id=recipe_id,
            rating=rating,
            image_url=image_url,
            duration_minutes=duration_minutes
        )

        return MessageResponse(message="Recipe marked as cooked")

    except Exception as e:
        logger.error(f"Error marking recipe as cooked: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark recipe as cooked: {str(e)}"
        )


@router.patch("/cooking-events/{event_id}", response_model=CookingEventResponse)
async def update_cooking_event(
    event_id: str,
    request: UpdateCookingEventRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Update a cooking event.

    Only the owner can update their own events.
    Can update:
    - cooked_at: When the cooking happened
    - rating: Rating given for this session (0.5-5.0)
    - image_url: Photo from cooking (set to null to remove)
    """
    from app.services.upload_service import UploadService

    try:
        repo = UserRecipeRepository(supabase)
        upload_service = UploadService(supabase)

        # Check if we need to remove the existing image
        remove_image = False
        old_image_url = None

        if request.image_url is None:
            # Check if this is an explicit null (remove image) vs not provided
            # We need to check the raw request to distinguish
            existing = await repo.get_cooking_event(event_id, current_user["id"])
            if existing and existing.get("image_url"):
                # User wants to remove the image
                remove_image = True
                old_image_url = existing["image_url"]

        # Update the event
        updated = await repo.update_cooking_event(
            event_id=event_id,
            user_id=current_user["id"],
            cooked_at=request.cooked_at,
            rating=request.rating,
            image_url=request.image_url if request.image_url else None,
            remove_image=remove_image
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cooking event not found or you don't have permission to edit it"
            )

        # If we removed the image, delete it from storage
        if remove_image and old_image_url:
            path = UploadService.extract_storage_path(old_image_url, "cooking-events")
            if path:
                try:
                    await upload_service.delete_image(path, bucket="cooking-events")
                except Exception as e:
                    logger.warning(f"Failed to delete old cooking image: {str(e)}")

        # Generate signed URL for cooking photo if present
        cooking_image_url = None
        if updated.get("image_url"):
            path = UploadService.extract_storage_path(updated["image_url"], "cooking-events")
            if path:
                cooking_image_url = upload_service.create_signed_url(
                    bucket="cooking-events",
                    path=path,
                    expires_in=3600
                )

        return CookingEventResponse(
            event_id=updated["id"],
            recipe_id=updated["recipe_id"],
            cooked_at=updated["cooked_at"],
            rating=updated.get("rating"),
            cooking_image_url=cooking_image_url,
            duration_minutes=updated.get("duration_minutes")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cooking event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cooking event: {str(e)}"
        )


@router.delete("/cooking-events/{event_id}", response_model=MessageResponse)
async def delete_cooking_event(
    event_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Delete a cooking event.

    Only the owner can delete their own events.
    Also:
    - Decrements times_cooked in user_recipe_data
    - Deletes associated image from storage if exists
    """
    from app.services.upload_service import UploadService

    try:
        repo = UserRecipeRepository(supabase)
        upload_service = UploadService(supabase)

        # Delete the event (returns the deleted event data)
        deleted = await repo.delete_cooking_event(
            event_id=event_id,
            user_id=current_user["id"]
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cooking event not found or you don't have permission to delete it"
            )

        # If there was an image, delete it from storage
        if deleted.get("image_url"):
            path = UploadService.extract_storage_path(deleted["image_url"], "cooking-events")
            if path:
                try:
                    await upload_service.delete_image(path, bucket="cooking-events")
                except Exception as e:
                    logger.warning(f"Failed to delete cooking image: {str(e)}")

        return MessageResponse(message="Cooking event deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cooking event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cooking event: {str(e)}"
        )


@router.post("/search", response_model=List[RecipeListItemResponse])
async def search_recipes_ai(
    search: RecipeSearchRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """Natural language recipe search using AI (legacy endpoint)"""
    try:
        repo = RecipeRepository(supabase)
        openai_service = OpenAIService()

        user_id = current_user["id"] if current_user else None

        # Get all accessible recipes
        recipes = await repo.get_public_recipes(limit=100)

        # Use AI to rank recipes based on query
        ranked_ids = openai_service.natural_language_search(
            search.query,
            recipes,
            search.limit
        )

        # Get full recipe details for ranked results
        ranked_recipes = [r for r in recipes if r["id"] in ranked_ids]
        # Sort by rank order
        ranked_recipes.sort(key=lambda r: ranked_ids.index(r["id"]))

        # Batch enrich categories (avoids N+1 queries)
        ranked_recipes = await repo.enrich_with_category(ranked_recipes)

        return [await _format_list_item_response(r, user_id, supabase) for r in ranked_recipes]

    except Exception as e:
        logger.error(f"Error searching recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search recipes: {str(e)}"
        )


# Helper functions


async def _format_recipe_response(
    recipe: dict,
    user_id: Optional[str],
    supabase: Client
) -> RecipeResponse:
    """Format recipe dict into RecipeResponse"""
    # Get contributors
    contributors = recipe.get("contributors", [])
    contributor_responses = [
        RecipeContributorResponse(
            user_id=c.get("user_id"),
            display_name=c.get("display_name"),
            contribution_type=c["contribution_type"],
            order=c["order"]
        )
        for c in contributors
    ]

    # Get user data if authenticated
    user_data = None
    if user_id:
        user_repo = UserRecipeRepository(supabase)
        user_recipe_data = await user_repo.get_by_user_and_recipe(user_id, recipe["id"])
        if user_recipe_data:
            user_data = UserRecipeDataResponse(**user_recipe_data)

    # Build timings
    timings = None
    if recipe.get("prep_time_minutes") or recipe.get("cook_time_minutes") or recipe.get("resting_time_minutes"):
        timings = RecipeTimings(
            prep_time_minutes=recipe.get("prep_time_minutes"),
            cook_time_minutes=recipe.get("cook_time_minutes"),
            resting_time_minutes=recipe.get("resting_time_minutes"),
            total_time_minutes=recipe.get("total_time_minutes")
        )

    # Get video platform if recipe is from a video
    video_platform = None
    if recipe.get("source_type") in ("video", "link"):
        from app.repositories.video_source_repository import VideoSourceRepository
        video_repo = VideoSourceRepository(supabase)
        video_source = await video_repo.get_by_recipe(recipe["id"])
        if video_source:
            video_platform = video_source.get("platform")

    # Get category data if category_id is set
    category = None
    if recipe.get("category_id"):
        repo = RecipeRepository(supabase)
        enriched = await repo.enrich_with_category([recipe])
        if enriched and enriched[0].get("category"):
            cat = enriched[0]["category"]
            category = RecipeCategoryResponse(
                id=cat["id"],
                slug=cat["slug"]
            )

    return RecipeResponse(
        id=recipe["id"],
        title=recipe["title"],
        description=recipe.get("description"),
        image_url=recipe.get("image_url"),
        ingredients=[Ingredient(**ing) for ing in recipe.get("ingredients", [])],
        instructions=[Instruction(**inst) for inst in recipe.get("instructions", [])],
        servings=recipe.get("servings"),
        difficulty=recipe.get("difficulty"),
        tags=recipe.get("tags", []),
        category=category,
        timings=timings,
        source_type=recipe["source_type"],
        source_url=recipe.get("source_url"),
        created_by=recipe["created_by"],
        original_recipe_id=recipe.get("original_recipe_id"),
        fork_count=recipe.get("fork_count", 0),
        # Rating aggregation fields
        average_rating=recipe.get("average_rating"),
        rating_count=recipe.get("rating_count", 0),
        rating_distribution=recipe.get("rating_distribution"),
        is_public=recipe["is_public"],
        contributors=contributor_responses,
        user_data=user_data,
        video_platform=video_platform,
        created_at=recipe["created_at"],
        updated_at=recipe["updated_at"]
    )


async def _format_list_item_response(
    recipe: dict,
    user_id: Optional[str],
    supabase: Client,
    user_recipe_data: Optional[Dict[str, Any]] = None
) -> RecipeListItemResponse:
    """
    Format recipe dict into RecipeListItemResponse

    Args:
        recipe: Recipe data from database
        user_id: Current user ID (if authenticated)
        supabase: Supabase client
        user_recipe_data: Pre-fetched user data (optional, for batch operations)
    """
    # Get user data if authenticated
    user_rating = None
    is_favorite = False

    if user_id and user_recipe_data is None:
        # Fallback to single query if data not pre-fetched
        user_repo = UserRecipeRepository(supabase)
        user_recipe_data = await user_repo.get_by_user_and_recipe(user_id, recipe["id"])

    if user_recipe_data:
        user_rating = user_recipe_data.get("rating")
        is_favorite = user_recipe_data.get("is_favorite", False)

    timings = None
    if recipe.get("prep_time_minutes") or recipe.get("cook_time_minutes") or recipe.get("resting_time_minutes"):
        timings = RecipeTimings(
            prep_time_minutes=recipe.get("prep_time_minutes"),
            cook_time_minutes=recipe.get("cook_time_minutes"),
            resting_time_minutes=recipe.get("resting_time_minutes"),
            total_time_minutes=recipe.get("total_time_minutes")
        )

    # Get video platform if recipe is from a video
    video_platform = None
    if recipe.get("source_type") in ("video", "link"):
        from app.repositories.video_source_repository import VideoSourceRepository
        video_repo = VideoSourceRepository(supabase)
        video_source = await video_repo.get_by_recipe(recipe["id"])
        if video_source:
            video_platform = video_source.get("platform")

    # Get category data if pre-enriched or category_id is set
    category = None
    if recipe.get("category"):
        # Already enriched
        cat = recipe["category"]
        category = RecipeCategoryResponse(
            id=cat["id"],
            slug=cat["slug"]
        )
    elif recipe.get("category_id"):
        # Need to fetch category
        repo = RecipeRepository(supabase)
        enriched = await repo.enrich_with_category([recipe])
        if enriched and enriched[0].get("category"):
            cat = enriched[0]["category"]
            category = RecipeCategoryResponse(
                id=cat["id"],
                slug=cat["slug"]
            )

    return RecipeListItemResponse(
        id=recipe["id"],
        title=recipe["title"],
        description=recipe.get("description"),
        image_url=recipe.get("image_url"),
        servings=recipe.get("servings"),
        difficulty=recipe.get("difficulty"),
        tags=recipe.get("tags", []),
        category=category,
        timings=timings,
        created_by=recipe["created_by"],
        is_public=recipe["is_public"],
        fork_count=recipe.get("fork_count", 0),
        user_rating=user_rating,
        is_favorite=is_favorite,
        video_platform=video_platform,
        created_at=recipe["created_at"]
    )


# ============= NEW ENDPOINTS: Timings & Rating =============


@router.patch("/{recipe_id}/timings", response_model=RecipeTimingsUpdateResponse)
async def update_recipe_timings(
    recipe_id: str,
    data: RecipeTimingsUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update recipe timings with smart ownership logic.

    - If you OWN the recipe: Updates base recipe (visible to all users)
    - If you DON'T own it: Updates your personal custom timings

    Returns which type of update was performed.
    """
    from app.services.recipe_service import RecipeService
    from app.core.database import get_supabase_admin_client

    # Use admin client to bypass RLS (we already validated user auth)
    service = RecipeService(get_supabase_admin_client())

    try:
        result = await service.update_recipe_timings(
            recipe_id=recipe_id,
            user_id=current_user["id"],
            prep_time_minutes=data.prep_time_minutes,
            cook_time_minutes=data.cook_time_minutes,
            resting_time_minutes=data.resting_time_minutes
        )

        return RecipeTimingsUpdateResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating recipe timings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update recipe timings")


@router.patch("/{recipe_id}/rating", response_model=RecipeResponse)
async def update_recipe_rating(
    recipe_id: str,
    data: RecipeRatingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Rate a recipe with half-star precision (0.5, 1.0, 1.5, ..., 5.0).

    Automatically updates:
    - Your personal rating
    - Recipe's average rating
    - Recipe's rating count
    - Recipe's rating distribution

    Returns the complete updated recipe with your rating and updated aggregate stats.
    """
    from app.services.recipe_service import RecipeService
    from app.repositories.recipe_repository import RecipeRepository
    from app.core.database import get_supabase_admin_client

    # Use admin client to bypass RLS (we already validated user auth)
    supabase = get_supabase_admin_client()
    service = RecipeService(supabase)
    repo = RecipeRepository(supabase)

    try:
        # Update the rating
        await service.update_recipe_rating(
            recipe_id=recipe_id,
            user_id=current_user["id"],
            rating=data.rating
        )

        # Fetch the updated recipe
        updated_recipe = await repo.get_by_id(recipe_id)
        if not updated_recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        # Return formatted response with user data
        return await _format_recipe_response(updated_recipe, current_user["id"], supabase)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating recipe rating: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update recipe rating")
