"""
Recipe endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List, Optional
import logging

from app.core.database import get_supabase_client
from app.core.security import get_current_user, get_current_user_optional
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.user_recipe_repository import UserRecipeRepository
from app.services.openai_service import OpenAIService
from app.api.v1.schemas.recipe import (
    RecipeCreateRequest,
    RecipeUpdateRequest,
    RecipeForkRequest,
    RecipeRatingRequest,
    UserRecipeDataUpdate,
    RecipeSearchRequest,
    RecipeResponse,
    RecipeListItemResponse,
    UserRecipeDataResponse,
    RecipeContributorResponse
)
from app.api.v1.schemas.common import MessageResponse
from app.domain.models import RecipeTimings, Ingredient, Instruction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreateRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new recipe manually"""
    try:
        repo = RecipeRepository(supabase)

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
            "categories": recipe_data.categories,
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


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a recipe by ID"""
    try:
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

        return await _format_recipe_response(recipe, user_id, supabase)

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
    categories: Optional[str] = None,  # Comma-separated
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
        if categories:
            filters["categories"] = categories.split(",")

        recipes = await repo.get_public_recipes(limit, offset, filters)

        user_id = current_user["id"] if current_user else None
        return [await _format_list_item_response(r, user_id, supabase) for r in recipes]

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

        return [await _format_list_item_response(r, current_user["id"], supabase) for r in recipes]

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
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a recipe"""
    try:
        repo = RecipeRepository(supabase)

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
        if update_data.categories is not None:
            data["categories"] = update_data.categories
        if update_data.timings is not None:
            data["prep_time_minutes"] = update_data.timings.prep_time_minutes
            data["cook_time_minutes"] = update_data.timings.cook_time_minutes
            data["total_time_minutes"] = update_data.timings.total_time_minutes
        if update_data.is_public is not None:
            data["is_public"] = update_data.is_public

        updated_recipe = await repo.update(recipe_id, data)

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
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a recipe"""
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

        await repo.delete(recipe_id)

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
    current_user: dict = Depends(get_current_user),
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
            "categories": original["categories"],
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
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Mark a recipe as cooked (increments cooked count)"""
    try:
        repo = UserRecipeRepository(supabase)
        await repo.increment_cooked_count(current_user["id"], recipe_id)

        return MessageResponse(message="Recipe marked as cooked")

    except Exception as e:
        logger.error(f"Error marking recipe as cooked: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark recipe as cooked: {str(e)}"
        )


@router.post("/search", response_model=List[RecipeListItemResponse])
async def search_recipes(
    search: RecipeSearchRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    supabase: Client = Depends(get_supabase_client)
):
    """Natural language recipe search using AI"""
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
            user_id=c["user_id"],
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
    if recipe.get("prep_time_minutes") or recipe.get("cook_time_minutes"):
        timings = RecipeTimings(
            prep_time_minutes=recipe.get("prep_time_minutes"),
            cook_time_minutes=recipe.get("cook_time_minutes"),
            total_time_minutes=recipe.get("total_time_minutes")
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
        categories=recipe.get("categories", []),
        timings=timings,
        source_type=recipe["source_type"],
        source_url=recipe.get("source_url"),
        created_by=recipe["created_by"],
        original_recipe_id=recipe.get("original_recipe_id"),
        fork_count=recipe.get("fork_count", 0),
        is_public=recipe["is_public"],
        contributors=contributor_responses,
        user_data=user_data,
        created_at=recipe["created_at"],
        updated_at=recipe["updated_at"]
    )


async def _format_list_item_response(
    recipe: dict,
    user_id: Optional[str],
    supabase: Client
) -> RecipeListItemResponse:
    """Format recipe dict into RecipeListItemResponse"""
    # Get user data if authenticated
    user_rating = None
    is_favorite = False

    if user_id:
        user_repo = UserRecipeRepository(supabase)
        user_recipe_data = await user_repo.get_by_user_and_recipe(user_id, recipe["id"])
        if user_recipe_data:
            user_rating = user_recipe_data.get("rating")
            is_favorite = user_recipe_data.get("is_favorite", False)

    timings = None
    if recipe.get("prep_time_minutes") or recipe.get("cook_time_minutes"):
        timings = RecipeTimings(
            prep_time_minutes=recipe.get("prep_time_minutes"),
            cook_time_minutes=recipe.get("cook_time_minutes"),
            total_time_minutes=recipe.get("total_time_minutes")
        )

    return RecipeListItemResponse(
        id=recipe["id"],
        title=recipe["title"],
        description=recipe.get("description"),
        image_url=recipe.get("image_url"),
        servings=recipe.get("servings"),
        difficulty=recipe.get("difficulty"),
        tags=recipe.get("tags", []),
        categories=recipe.get("categories", []),
        timings=timings,
        created_by=recipe["created_by"],
        is_public=recipe["is_public"],
        fork_count=recipe.get("fork_count", 0),
        user_rating=user_rating,
        is_favorite=is_favorite,
        created_at=recipe["created_at"]
    )
