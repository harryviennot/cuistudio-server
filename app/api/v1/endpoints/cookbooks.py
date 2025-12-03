"""
Cookbook endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import List
import logging

from app.core.database import get_supabase_client
from app.core.security import get_current_user, get_authenticated_user
from app.repositories.cookbook_repository import CookbookRepository, CookbookFolderRepository
from app.api.v1.schemas.cookbook import (
    CookbookCreateRequest,
    CookbookUpdateRequest,
    CookbookAddRecipeRequest,
    FolderCreateRequest,
    FolderUpdateRequest,
    CookbookResponse,
    CookbookDetailResponse,
    FolderResponse
)
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cookbooks", tags=["Cookbooks"])


@router.post("", response_model=CookbookResponse, status_code=status.HTTP_201_CREATED)
async def create_cookbook(
    cookbook_data: CookbookCreateRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new cookbook"""
    try:
        repo = CookbookRepository(supabase)

        data = {
            "user_id": current_user["id"],
            "title": cookbook_data.title,
            "subtitle": cookbook_data.subtitle,
            "description": cookbook_data.description,
            "image_url": cookbook_data.image_url,
            "is_public": cookbook_data.is_public
        }

        cookbook = await repo.create(data)

        return CookbookResponse(**cookbook)

    except Exception as e:
        logger.error(f"Error creating cookbook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cookbook: {str(e)}"
        )


@router.get("", response_model=List[CookbookResponse])
async def list_cookbooks(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """List user's cookbooks"""
    try:
        repo = CookbookRepository(supabase)
        cookbooks = await repo.get_user_cookbooks(current_user["id"], limit, offset)

        return [CookbookResponse(**cb) for cb in cookbooks]

    except Exception as e:
        logger.error(f"Error listing cookbooks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cookbooks: {str(e)}"
        )


@router.get("/{cookbook_id}", response_model=CookbookDetailResponse)
async def get_cookbook(
    cookbook_id: str,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get cookbook with all details (folders and recipes)"""
    try:
        repo = CookbookRepository(supabase)
        cookbook = await repo.get_with_details(cookbook_id)

        if not cookbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cookbook not found"
            )

        # Check access permissions
        if cookbook["user_id"] != current_user["id"] and not cookbook["is_public"]:
            # Check if shared
            share_check = await supabase.table("cookbook_shares")\
                .select("id")\
                .eq("cookbook_id", cookbook_id)\
                .eq("shared_with_user_id", current_user["id"])\
                .execute()

            if not share_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this cookbook"
                )

        return CookbookDetailResponse(**cookbook)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cookbook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cookbook: {str(e)}"
        )


@router.put("/{cookbook_id}", response_model=CookbookResponse)
async def update_cookbook(
    cookbook_id: str,
    update_data: CookbookUpdateRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a cookbook"""
    try:
        repo = CookbookRepository(supabase)

        # Check ownership
        cookbook = await repo.get_by_id(cookbook_id)
        if not cookbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cookbook not found"
            )

        if cookbook["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this cookbook"
            )

        # Prepare update data
        data = {}
        if update_data.title is not None:
            data["title"] = update_data.title
        if update_data.subtitle is not None:
            data["subtitle"] = update_data.subtitle
        if update_data.description is not None:
            data["description"] = update_data.description
        if update_data.image_url is not None:
            data["image_url"] = update_data.image_url
        if update_data.is_public is not None:
            data["is_public"] = update_data.is_public

        updated_cookbook = await repo.update(cookbook_id, data)

        return CookbookResponse(**updated_cookbook)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cookbook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cookbook: {str(e)}"
        )


@router.delete("/{cookbook_id}", response_model=MessageResponse)
async def delete_cookbook(
    cookbook_id: str,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a cookbook"""
    try:
        repo = CookbookRepository(supabase)

        # Check ownership
        cookbook = await repo.get_by_id(cookbook_id)
        if not cookbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cookbook not found"
            )

        if cookbook["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this cookbook"
            )

        await repo.delete(cookbook_id)

        return MessageResponse(message="Cookbook deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cookbook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cookbook: {str(e)}"
        )


@router.post("/{cookbook_id}/recipes", response_model=MessageResponse)
async def add_recipe_to_cookbook(
    cookbook_id: str,
    recipe_data: CookbookAddRecipeRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Add a recipe to a cookbook"""
    try:
        repo = CookbookRepository(supabase)

        # Check ownership
        cookbook = await repo.get_by_id(cookbook_id)
        if not cookbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cookbook not found"
            )

        if cookbook["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this cookbook"
            )

        await repo.add_recipe(cookbook_id, recipe_data.recipe_id, recipe_data.folder_id)

        return MessageResponse(message="Recipe added to cookbook")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding recipe to cookbook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add recipe to cookbook: {str(e)}"
        )


@router.delete("/{cookbook_id}/recipes/{recipe_id}", response_model=MessageResponse)
async def remove_recipe_from_cookbook(
    cookbook_id: str,
    recipe_id: str,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Remove a recipe from a cookbook"""
    try:
        repo = CookbookRepository(supabase)

        # Check ownership
        cookbook = await repo.get_by_id(cookbook_id)
        if not cookbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cookbook not found"
            )

        if cookbook["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this cookbook"
            )

        await repo.remove_recipe(cookbook_id, recipe_id)

        return MessageResponse(message="Recipe removed from cookbook")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing recipe from cookbook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove recipe from cookbook: {str(e)}"
        )


@router.post("/{cookbook_id}/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    cookbook_id: str,
    folder_data: FolderCreateRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a folder in a cookbook"""
    try:
        repo = CookbookRepository(supabase)

        # Check ownership
        cookbook = await repo.get_by_id(cookbook_id)
        if not cookbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cookbook not found"
            )

        if cookbook["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this cookbook"
            )

        folder_repo = CookbookFolderRepository(supabase)

        data = {
            "cookbook_id": cookbook_id,
            "name": folder_data.name,
            "parent_folder_id": folder_data.parent_folder_id
        }

        folder = await folder_repo.create(data)

        return FolderResponse(**folder)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create folder: {str(e)}"
        )


@router.put("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: str,
    update_data: FolderUpdateRequest,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a folder"""
    try:
        folder_repo = CookbookFolderRepository(supabase)

        # Get folder and check ownership
        folder = await folder_repo.get_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )

        cookbook_repo = CookbookRepository(supabase)
        cookbook = await cookbook_repo.get_by_id(folder["cookbook_id"])

        if cookbook["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this folder"
            )

        updated_folder = await folder_repo.update(folder_id, {"name": update_data.name})

        return FolderResponse(**updated_folder)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update folder: {str(e)}"
        )


@router.delete("/folders/{folder_id}", response_model=MessageResponse)
async def delete_folder(
    folder_id: str,
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a folder"""
    try:
        folder_repo = CookbookFolderRepository(supabase)

        # Get folder and check ownership
        folder = await folder_repo.get_by_id(folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )

        cookbook_repo = CookbookRepository(supabase)
        cookbook = await cookbook_repo.get_by_id(folder["cookbook_id"])

        if cookbook["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this folder"
            )

        await folder_repo.delete(folder_id)

        return MessageResponse(message="Folder deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete folder: {str(e)}"
        )
