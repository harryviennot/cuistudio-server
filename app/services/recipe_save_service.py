"""
Recipe Save Service
Handles the unified save logic for all extraction types.
This separates the "save" action from the "extract" action.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from supabase import Client

from app.domain.enums import SourceType
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.collection_repository import CollectionRepository
from app.repositories.collection_recipe_repository import CollectionRecipeRepository
from app.repositories.video_source_repository import VideoSourceRepository
from app.repositories.video_creator_repository import VideoCreatorRepository
from app.services.video_url_parser import VideoURLParser

logger = logging.getLogger(__name__)


class RecipeSaveService:
    """
    Unified service for saving recipes from extractions.

    This service handles:
    1. Publishing draft recipes (setting is_draft=false)
    2. Adding recipes to user's collections
    3. Creating video_source and video_creator records for video extractions
    4. Handling duplicate video saves (add existing to collection)
    """

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.recipe_repo = RecipeRepository(supabase)
        self.collection_repo = CollectionRepository(supabase)
        self.collection_recipe_repo = CollectionRecipeRepository(supabase)
        self.video_source_repo = VideoSourceRepository(supabase)
        self.video_creator_repo = VideoCreatorRepository(supabase)

    async def save_recipe_to_collection(
        self,
        user_id: str,
        recipe_id: str,
        collection_id: str
    ) -> Dict[str, Any]:
        """
        Save a recipe to a collection. If recipe is a draft owned by user, publish it.

        This is the main entry point for saving recipes after preview.

        Args:
            user_id: User saving the recipe
            recipe_id: Recipe ID to save
            collection_id: Collection ID to save to

        Returns:
            Dict with recipe_id, collection_id, added_to_collection, was_draft
        """
        try:
            # Get the recipe
            recipe = await self.recipe_repo.get_by_id(recipe_id)
            if not recipe:
                raise ValueError(f"Recipe not found: {recipe_id}")

            # Verify collection exists and belongs to user
            collection = await self.collection_repo.get_by_id(collection_id)
            if not collection:
                raise ValueError(f"Collection not found: {collection_id}")
            if collection["user_id"] != user_id:
                raise PermissionError("You don't own this collection")

            # Track if this was a draft
            was_draft = recipe.get("is_draft", False) and recipe["created_by"] == user_id

            # If recipe is a draft owned by this user, publish it
            if was_draft:
                await self.recipe_repo.update(recipe_id, {"is_draft": False})
                logger.info(f"Published draft recipe {recipe_id}")

            # Check if user can access this recipe (public or owned by user)
            if not recipe["is_public"] and recipe["created_by"] != user_id:
                raise PermissionError("You don't have access to this recipe")

            # Add to collection
            result = await self.collection_recipe_repo.add_recipe_to_collection(
                collection_id=collection_id,
                recipe_id=recipe_id
            )

            return {
                "recipe_id": recipe_id,
                "collection_id": collection_id,
                "added_to_collection": result is not None,
                "was_draft": was_draft
            }

        except Exception as e:
            logger.error(f"Error saving recipe {recipe_id} to collection: {str(e)}")
            raise

    async def save_from_job(
        self,
        user_id: str,
        job_id: str,
        collection_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a recipe from an extraction job to a collection.

        This is called when the extraction created a draft recipe that the user wants to keep.

        Args:
            user_id: User saving the recipe
            job_id: Extraction job ID
            collection_id: Collection to save to (defaults to 'extracted' collection)

        Returns:
            Dict with recipe_id, collection_id, added_to_collection
        """
        try:
            # Get extraction job
            job = self.supabase.table("extraction_jobs")\
                .select("*")\
                .eq("id", job_id)\
                .execute()

            if not job.data:
                raise ValueError(f"Extraction job not found: {job_id}")

            job_data = job.data[0]

            # Check if job belongs to user
            if job_data["user_id"] != user_id:
                raise PermissionError("You don't have permission to save this extraction")

            # Check if job has a recipe_id (draft was created during extraction)
            if not job_data.get("recipe_id"):
                raise ValueError("Extraction job has no associated recipe")

            recipe_id = job_data["recipe_id"]

            # If no collection specified, use the user's 'extracted' collection
            if not collection_id:
                extracted_collection = await self.collection_repo.get_by_slug(user_id, "extracted")
                if not extracted_collection:
                    # Create default collections if they don't exist
                    await self.collection_repo.create_default_collections(user_id)
                    extracted_collection = await self.collection_repo.get_by_slug(user_id, "extracted")
                collection_id = extracted_collection["id"]

            return await self.save_recipe_to_collection(
                user_id=user_id,
                recipe_id=recipe_id,
                collection_id=collection_id
            )

        except Exception as e:
            logger.error(f"Error saving recipe from job {job_id}: {str(e)}")
            raise

    async def add_existing_to_collection(
        self,
        user_id: str,
        recipe_id: str,
        collection_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add an existing recipe to user's collection.

        Used when:
        - User extracts a video that was already extracted by someone else
        - User wants to save a public recipe to their collection

        Args:
            user_id: User saving the recipe
            recipe_id: Existing recipe ID
            collection_id: Collection to save to (defaults to 'saved' collection)

        Returns:
            Dict with recipe_id, collection_id, added_to_collection
        """
        try:
            # Verify recipe exists and is accessible
            recipe = await self.recipe_repo.get_by_id(recipe_id)
            if not recipe:
                raise ValueError(f"Recipe not found: {recipe_id}")

            # Check if user can access this recipe
            if not recipe["is_public"] and recipe["created_by"] != user_id:
                raise PermissionError("You don't have access to this recipe")

            # If no collection specified, use the user's 'saved' collection
            if not collection_id:
                saved_collection = await self.collection_repo.get_by_slug(user_id, "saved")
                if not saved_collection:
                    # Create default collections if they don't exist
                    await self.collection_repo.create_default_collections(user_id)
                    saved_collection = await self.collection_repo.get_by_slug(user_id, "saved")
                collection_id = saved_collection["id"]

            # Add to collection (will not duplicate if already exists)
            result = await self.collection_recipe_repo.add_recipe_to_collection(
                collection_id=collection_id,
                recipe_id=recipe_id
            )

            return {
                "recipe_id": recipe_id,
                "collection_id": collection_id,
                "added_to_collection": result is not None
            }

        except Exception as e:
            logger.error(f"Error adding recipe {recipe_id} to collection: {str(e)}")
            raise

    async def create_draft_recipe(
        self,
        user_id: str,
        source_type: SourceType,
        extracted_data: Dict[str, Any],
        video_metadata: Optional[Dict[str, Any]] = None,
        source_url: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a draft recipe from extraction data.

        Draft recipes are not visible to others and are not added to collections.
        The user must explicitly save the recipe to publish it.

        Args:
            user_id: User creating the recipe
            source_type: Type of source (video, photo, etc.)
            extracted_data: Normalized recipe data from extraction
            video_metadata: Video-specific metadata (for video extractions)
            source_url: Original source URL
            job_id: Optional job ID to link

        Returns:
            Dict with recipe_id and recipe data
        """
        try:
            # Determine image source
            image_source = None
            if source_type == SourceType.VIDEO and video_metadata:
                image_source = "video_thumbnail"
            elif source_type == SourceType.LINK and not video_metadata:
                # LINK type without video metadata = webpage extraction
                image_source = "scraped"
            elif extracted_data.get("image_url"):
                image_source = "generated"

            # Default to public for all extractions
            # User can change privacy settings later if desired
            is_public = True

            # Clean source URL for video extractions (remove tracking params)
            clean_source_url = source_url
            if source_url and video_metadata:
                # Video URLs (either VIDEO or LINK type with video) should be cleaned
                clean_source_url = VideoURLParser.clean_url(source_url)

            # Prepare recipe data - as DRAFT
            recipe_data = {
                "title": extracted_data["title"],
                "description": extracted_data.get("description"),
                "ingredients": extracted_data.get("ingredients", []),
                "instructions": extracted_data.get("instructions", []),
                "servings": extracted_data.get("servings"),
                "difficulty": extracted_data.get("difficulty"),
                "tags": extracted_data.get("tags", []),
                "categories": extracted_data.get("categories", []),
                "prep_time_minutes": extracted_data.get("prep_time_minutes"),
                "cook_time_minutes": extracted_data.get("cook_time_minutes"),
                "total_time_minutes": extracted_data.get("total_time_minutes"),
                "source_type": source_type.value,
                "source_url": clean_source_url,
                "image_url": extracted_data.get("image_url"),
                "image_source": image_source,
                "created_by": user_id,
                "is_public": is_public,
                "is_draft": True  # Draft until user saves
            }

            # Create recipe
            recipe = await self.recipe_repo.create(recipe_data)
            recipe_id = recipe["id"]

            # Create contributor record
            self.supabase.table("recipe_contributors").insert({
                "recipe_id": recipe_id,
                "user_id": user_id,
                "contribution_type": "creator",
                "order": 0
            }).execute()

            # Create video-specific records if video metadata present
            # We await this to ensure video_sources table is populated before returning
            # This allows the recipe endpoint to query for video_platform immediately
            if video_metadata:
                await self._create_video_records_background(
                    recipe_id=recipe_id,
                    video_metadata=video_metadata,
                    source_url=source_url
                )

            # Update job with recipe_id if provided
            if job_id:
                self.supabase.table("extraction_jobs")\
                    .update({
                        "recipe_id": recipe_id,
                        "status": "completed"
                    })\
                    .eq("id", job_id)\
                    .execute()

            logger.info(f"Created draft recipe {recipe_id} from {source_type.value} extraction")

            return {
                "recipe_id": recipe_id,
                "recipe": recipe
            }

        except Exception as e:
            logger.error(f"Error creating draft recipe from extraction: {str(e)}")
            raise

    async def delete_draft_recipe(
        self,
        user_id: str,
        recipe_id: str
    ) -> bool:
        """
        Delete a draft recipe.

        Only draft recipes owned by the user can be deleted.

        Args:
            user_id: User requesting deletion
            recipe_id: Recipe ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            # Get the recipe
            recipe = await self.recipe_repo.get_by_id(recipe_id)
            if not recipe:
                raise ValueError(f"Recipe not found: {recipe_id}")

            # Check ownership
            if recipe["created_by"] != user_id:
                raise PermissionError("You don't own this recipe")

            # Only drafts can be deleted
            if not recipe.get("is_draft"):
                raise PermissionError("Only draft recipes can be deleted")

            # Delete the recipe (cascade will handle related records)
            result = await self.recipe_repo.delete(recipe_id)
            if result:
                logger.info(f"Deleted draft recipe {recipe_id}")

            return result

        except Exception as e:
            logger.error(f"Error deleting draft recipe {recipe_id}: {str(e)}")
            raise

    async def _create_video_records_background(
        self,
        recipe_id: str,
        video_metadata: Dict[str, Any],
        source_url: Optional[str]
    ):
        """
        Background wrapper for video records creation.
        Catches all exceptions to prevent unhandled errors in fire-and-forget tasks.
        """
        try:
            await self._create_video_records(recipe_id, video_metadata, source_url)
        except Exception as e:
            # Log but don't propagate - this is a background task
            logger.error(f"Background video records creation failed for recipe {recipe_id}: {str(e)}")

    async def _create_video_records(
        self,
        recipe_id: str,
        video_metadata: Dict[str, Any],
        source_url: Optional[str]
    ):
        """
        Create video_source and video_creator records for a video extraction.

        Args:
            recipe_id: Recipe ID to link to
            video_metadata: Video metadata from extraction
            source_url: Original source URL
        """
        try:
            platform = video_metadata.get("platform")
            platform_video_id = video_metadata.get("platform_video_id")

            if not platform or not platform_video_id:
                logger.warning("Missing platform or video ID in video metadata")
                return

            # Create or get video creator
            video_creator_id = None
            creator_info = video_metadata.get("creator", {})
            if creator_info.get("platform_user_id"):
                creator = await self.video_creator_repo.get_or_create(
                    platform=platform,
                    platform_user_id=creator_info["platform_user_id"],
                    platform_username=creator_info.get("platform_username"),
                    display_name=creator_info.get("display_name"),
                    profile_url=creator_info.get("profile_url")
                )
                video_creator_id = creator["id"]

                # Note: We don't add video_creator as a contributor here because
                # the platform_user_id is not a valid UUID. The video_creator_id
                # in video_sources table provides the attribution link instead.

            # Create video source
            await self.video_source_repo.create_video_source(
                platform=platform,
                platform_video_id=platform_video_id,
                recipe_id=recipe_id,
                original_url=source_url or video_metadata.get("original_url", ""),
                canonical_url=video_metadata.get("canonical_url"),
                title=video_metadata.get("title"),
                description=video_metadata.get("description"),
                duration_seconds=video_metadata.get("duration_seconds"),
                thumbnail_url=video_metadata.get("thumbnail_url"),
                view_count=video_metadata.get("view_count"),
                like_count=video_metadata.get("like_count"),
                upload_date=video_metadata.get("upload_date"),
                video_creator_id=video_creator_id,
                raw_metadata=video_metadata.get("raw_metadata")
            )

            logger.info(f"Created video records for recipe {recipe_id}")

        except Exception as e:
            # Log but don't fail - video records are supplementary
            logger.error(f"Error creating video records: {str(e)}")
