"""
Collections endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List
import logging

from app.core.database import get_supabase_client, get_supabase_admin_client
from app.core.security import get_current_user
from app.repositories.collection_repository import CollectionRepository
from app.repositories.collection_recipe_repository import CollectionRecipeRepository
from app.services.recipe_save_service import RecipeSaveService
from app.api.v1.schemas.collection import (
    CollectionCreateRequest,
    CollectionUpdateRequest,
    CollectionResponse,
    CollectionListResponse,
    CollectionWithRecipesResponse,
    CollectionRecipeResponse,
    SaveRecipeRequest,
    SaveRecipeResponse,
)
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collections", tags=["Collections"])


@router.get("", response_model=CollectionListResponse)
async def list_collections(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    List all collections for the current user.

    Returns system collections (extracted, saved) and any custom collections.
    Collections are sorted by sort_order.
    """
    try:
        repo = CollectionRepository(supabase)
        collections = await repo.get_user_collections(current_user["id"])

        # Get recipe counts for each collection
        recipe_repo = CollectionRecipeRepository(supabase)
        collection_responses = []
        for c in collections:
            count = await recipe_repo.count_recipes_in_collection(c["id"])
            collection_responses.append(CollectionResponse(
                id=c["id"],
                name=c["name"],
                slug=c["slug"],
                description=c.get("description"),
                is_system=c["is_system"],
                sort_order=c["sort_order"],
                recipe_count=count,
                created_at=c["created_at"],
                updated_at=c["updated_at"]
            ))

        return CollectionListResponse(collections=collection_responses)

    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    request: CollectionCreateRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Create a new custom collection.

    System collections (extracted, saved) are created automatically.
    """
    try:
        repo = CollectionRepository(supabase)
        collection = await repo.create_collection(
            user_id=current_user["id"],
            name=request.name,
            description=request.description
        )

        return CollectionResponse(
            id=collection["id"],
            name=collection["name"],
            slug=collection["slug"],
            description=collection.get("description"),
            is_system=collection["is_system"],
            sort_order=collection["sort_order"],
            recipe_count=0,
            created_at=collection["created_at"],
            updated_at=collection["updated_at"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )


@router.get("/{collection_id}", response_model=CollectionWithRecipesResponse)
async def get_collection(
    collection_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get a collection with its recipes.
    """
    try:
        collection_repo = CollectionRepository(supabase)
        recipe_repo = CollectionRecipeRepository(supabase)

        # Get collection
        collection = await collection_repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

        # Check ownership
        if collection["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this collection"
            )

        # Get recipes
        recipes = await recipe_repo.get_collection_recipes(
            collection_id=collection_id,
            limit=limit,
            offset=offset
        )
        total_count = await recipe_repo.count_recipes_in_collection(collection_id)

        # Format recipes
        recipe_responses = [
            CollectionRecipeResponse(
                id=r["recipe"]["id"],
                title=r["recipe"]["title"],
                description=r["recipe"].get("description"),
                image_url=r["recipe"].get("image_url"),
                servings=r["recipe"].get("servings"),
                difficulty=r["recipe"].get("difficulty"),
                tags=r["recipe"].get("tags", []),
                source_type=r["recipe"]["source_type"],
                is_public=r["recipe"]["is_public"],
                added_at=r["added_at"],
                created_at=r["recipe"]["created_at"]
            )
            for r in recipes
        ]

        return CollectionWithRecipesResponse(
            collection=CollectionResponse(
                id=collection["id"],
                name=collection["name"],
                slug=collection["slug"],
                description=collection.get("description"),
                is_system=collection["is_system"],
                sort_order=collection["sort_order"],
                recipe_count=total_count,
                created_at=collection["created_at"],
                updated_at=collection["updated_at"]
            ),
            recipes=recipe_responses,
            total_count=total_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection: {str(e)}"
        )


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    request: CollectionUpdateRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update a collection.

    System collections can only have their description updated.
    """
    try:
        repo = CollectionRepository(supabase)

        # Get collection
        collection = await repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

        # Check ownership
        if collection["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this collection"
            )

        # Build update data
        update_data = {}
        if request.description is not None:
            update_data["description"] = request.description

        # Only allow name/sort_order updates for non-system collections
        if not collection["is_system"]:
            if request.name is not None:
                update_data["name"] = request.name
            if request.sort_order is not None:
                update_data["sort_order"] = request.sort_order
        elif request.name is not None or request.sort_order is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update name or sort order of system collections"
            )

        updated = await repo.update(collection_id, update_data)

        # Get recipe count
        recipe_repo = CollectionRecipeRepository(supabase)
        count = await recipe_repo.count_recipes_in_collection(collection_id)

        return CollectionResponse(
            id=updated["id"],
            name=updated["name"],
            slug=updated["slug"],
            description=updated.get("description"),
            is_system=updated["is_system"],
            sort_order=updated["sort_order"],
            recipe_count=count,
            created_at=updated["created_at"],
            updated_at=updated["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update collection: {str(e)}"
        )


@router.delete("/{collection_id}", response_model=MessageResponse)
async def delete_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete a collection.

    System collections cannot be deleted.
    Deleting a collection does NOT delete the recipes in it.
    """
    try:
        repo = CollectionRepository(supabase)

        # Get collection
        collection = await repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

        # Check ownership
        if collection["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this collection"
            )

        # Prevent deletion of system collections
        if collection["is_system"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete system collections"
            )

        await repo.delete(collection_id)

        return MessageResponse(message="Collection deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}"
        )


@router.post("/{collection_id}/recipes", response_model=SaveRecipeResponse)
async def add_recipe_to_collection(
    collection_id: str,
    request: SaveRecipeRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Add a recipe to a collection.

    If the recipe is a draft owned by the user, it will be published.
    """
    try:
        save_service = RecipeSaveService(supabase)

        result = await save_service.save_recipe_to_collection(
            user_id=current_user["id"],
            recipe_id=request.recipe_id,
            collection_id=collection_id
        )

        return SaveRecipeResponse(
            recipe_id=result["recipe_id"],
            collection_id=result["collection_id"],
            added_to_collection=result["added_to_collection"],
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
        logger.error(f"Error adding recipe to collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add recipe to collection: {str(e)}"
        )


@router.delete("/{collection_id}/recipes/{recipe_id}", response_model=MessageResponse)
async def remove_recipe_from_collection(
    collection_id: str,
    recipe_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Remove a recipe from a collection.

    This does NOT delete the recipe, just removes it from the collection.
    """
    try:
        collection_repo = CollectionRepository(supabase)
        recipe_repo = CollectionRecipeRepository(supabase)

        # Verify collection ownership
        collection = await collection_repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

        if collection["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this collection"
            )

        # Remove recipe from collection
        removed = await recipe_repo.remove_recipe_from_collection(
            collection_id=collection_id,
            recipe_id=recipe_id
        )

        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found in this collection"
            )

        return MessageResponse(message="Recipe removed from collection")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing recipe from collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove recipe from collection: {str(e)}"
        )
