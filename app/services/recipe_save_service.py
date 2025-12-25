"""
Recipe Save Service
Handles the unified save logic for all extraction types.
This separates the "save" action from the "extract" action.
"""
import logging
from typing import Dict, Any, Optional
from supabase import Client

from app.domain.enums import SourceType
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.user_recipe_repository import UserRecipeRepository
from app.repositories.video_source_repository import VideoSourceRepository
from app.repositories.video_creator_repository import VideoCreatorRepository
from app.repositories.category_repository import CategoryRepository
from app.services.video_url_parser import VideoURLParser
from app.services.thumbnail_cache_service import ThumbnailCacheService

logger = logging.getLogger(__name__)


class RecipeSaveService:
    """
    Unified service for saving recipes from extractions.

    This service handles:
    1. Publishing draft recipes (setting is_draft=false)
    2. Marking recipes as extracted in user_recipe_data
    3. Creating video_source and video_creator records for video extractions
    """

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.recipe_repo = RecipeRepository(supabase)
        self.user_recipe_repo = UserRecipeRepository(supabase)
        self.video_source_repo = VideoSourceRepository(supabase)
        self.video_creator_repo = VideoCreatorRepository(supabase)
        self.category_repo = CategoryRepository(supabase)
        self.thumbnail_cache = ThumbnailCacheService(supabase)

    async def publish_draft_recipe(
        self,
        user_id: str,
        recipe_id: str,
        is_public: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Publish a draft recipe and mark it as extracted.

        This is called when the user saves a recipe after previewing.
        It publishes the draft (is_draft=false) and ensures the user
        has a user_recipe_data record with was_extracted=true.

        Args:
            user_id: User saving the recipe
            recipe_id: Recipe ID to publish
            is_public: Whether the recipe should be publicly visible.
                       If None, defaults to True.

        Returns:
            Dict with recipe_id, was_draft, published
        """
        try:
            # Get the recipe
            recipe = await self.recipe_repo.get_by_id(recipe_id)
            if not recipe:
                raise ValueError(f"Recipe not found: {recipe_id}")

            # Track if this was a draft
            was_draft = recipe.get("is_draft", False)

            # Only the creator can publish their own draft
            if was_draft and recipe["created_by"] != user_id:
                raise PermissionError("You can only publish your own draft recipes")

            # Publish the draft if it is one
            if was_draft:
                # Determine final is_public value (default to True if not specified)
                final_is_public = is_public if is_public is not None else True
                await self.recipe_repo.update(recipe_id, {
                    "is_draft": False,
                    "is_public": final_is_public
                })
                logger.info(f"Published draft recipe {recipe_id} (is_public={final_is_public})")

            # Mark as extracted for this user
            await self.user_recipe_repo.mark_as_extracted(user_id, recipe_id)

            return {
                "recipe_id": recipe_id,
                "was_draft": was_draft,
                "published": was_draft  # True if we actually published something
            }

        except Exception as e:
            logger.error(f"Error publishing recipe {recipe_id}: {str(e)}")
            raise

    async def mark_recipe_extracted(
        self,
        user_id: str,
        recipe_id: str
    ) -> Dict[str, Any]:
        """
        Mark an existing recipe as extracted by this user.

        Used when a user extracts a duplicate URL - the recipe already exists
        but we need to mark it in their extracted collection.

        Args:
            user_id: User who extracted the recipe
            recipe_id: Existing recipe ID

        Returns:
            Dict with recipe_id and marked status
        """
        try:
            # Verify recipe exists
            recipe = await self.recipe_repo.get_by_id(recipe_id)
            if not recipe:
                raise ValueError(f"Recipe not found: {recipe_id}")

            # Mark as extracted
            await self.user_recipe_repo.mark_as_extracted(user_id, recipe_id)
            logger.info(f"Marked recipe {recipe_id} as extracted for user {user_id}")

            return {
                "recipe_id": recipe_id,
                "marked": True
            }

        except Exception as e:
            logger.error(f"Error marking recipe as extracted: {str(e)}")
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

        Note: We create a user_recipe_data record with was_extracted=true
        immediately when creating the draft. This ensures the recipe appears
        in the user's "Extracted" collection even before they publish it.

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

            # Resolve category_slug to category_id if provided
            category_id = None
            category_slug = extracted_data.get("category_slug")
            if category_slug:
                category_id = await self.category_repo.get_id_by_slug(category_slug)

            # Prepare recipe data - as DRAFT
            recipe_data = {
                "title": extracted_data["title"],
                "description": extracted_data.get("description"),
                "ingredients": extracted_data.get("ingredients", []),
                "instructions": extracted_data.get("instructions", []),
                "servings": extracted_data.get("servings"),
                "difficulty": extracted_data.get("difficulty"),
                "tags": extracted_data.get("tags", []),
                "category_id": category_id,
                "categories": extracted_data.get("categories", []),  # Keep for backwards compat
                "prep_time_minutes": extracted_data.get("prep_time_minutes"),
                "cook_time_minutes": extracted_data.get("cook_time_minutes"),
                "resting_time_minutes": extracted_data.get("resting_time_minutes"),
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

            # Mark as extracted in user_recipe_data
            # This ensures it appears in the user's "Extracted" collection
            await self.user_recipe_repo.mark_as_extracted(user_id, recipe_id)

            # Create video-specific records if video metadata present
            # We await this to ensure video_sources table is populated before returning
            # This allows the recipe endpoint to query for video_platform immediately
            if video_metadata:
                await self._create_video_records_background(
                    recipe_id=recipe_id,
                    video_metadata=video_metadata,
                    source_url=source_url
                )

                # Cache video thumbnail to Supabase Storage
                # This prevents broken images when platforms change thumbnail URLs
                thumbnail_url = video_metadata.get("thumbnail_url")
                if thumbnail_url:
                    cached_url = await self.thumbnail_cache.cache_thumbnail(
                        thumbnail_url=thumbnail_url,
                        recipe_id=recipe_id,
                        user_id=user_id
                    )
                    if cached_url:
                        # Update recipe with our cached thumbnail URL
                        await self.recipe_repo.update(recipe_id, {"image_url": cached_url})
                        logger.info(f"Cached video thumbnail for recipe {recipe_id}")

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
