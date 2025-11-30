"""
Extraction orchestrator service
Coordinates extraction from different sources and normalization
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Union, List
from supabase import Client

from app.domain.enums import SourceType, ExtractionStatus
from app.domain.exceptions import NotARecipeError, WebsiteBlockedError
from app.services.extractors.video_extractor import VideoExtractor
from app.services.extractors.photo_extractor import PhotoExtractor
from app.services.extractors.voice_extractor import VoiceExtractor
from app.services.extractors.paste_extractor import PasteExtractor
from app.services.extractors.link_extractor import LinkExtractor
from app.services.openai_service import OpenAIService
from app.services.flux_service import FluxService
from app.services.video_url_parser import VideoURLParser
from app.services.recipe_save_service import RecipeSaveService
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.video_source_repository import VideoSourceRepository
from app.core.events import get_event_broadcaster

logger = logging.getLogger(__name__)


class ExtractionService:
    """Orchestrates recipe extraction from various sources"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.openai_service = OpenAIService()
        self.flux_service = FluxService(supabase)
        self.recipe_repo = RecipeRepository(supabase)
        self.video_source_repo = VideoSourceRepository(supabase)
        self.recipe_save_service = RecipeSaveService(supabase)

    async def extract_and_create_recipe(
        self,
        user_id: str,
        source_type: SourceType,
        source: Union[str, List[str]],
        job_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Extract recipe from source(s) and create in database

        Args:
            user_id: User creating the recipe
            source_type: Type of source
            source: Source URL/content or list of URLs (for multi-image extraction)
            job_id: Optional extraction job ID for tracking
            progress_callback: Optional callback for progress updates

        Returns:
            Created recipe dict
        """
        try:
            # Update job status if provided
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.PROCESSING,
                    0,
                    "Starting extraction"
                )

            # Create progress callback that updates database if job_id is provided
            # Scale extractor progress (0-100%) to 0-50% range so service steps can use 50-100%
            def sync_progress_callback(percentage: int, step: str):
                """Synchronous wrapper for progress updates with scaling"""
                scaled_percentage = int(percentage * 0.5)
                if progress_callback:
                    progress_callback(scaled_percentage, step)
                if job_id:
                    # Schedule async update in event loop
                    asyncio.create_task(self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        scaled_percentage,
                        step
                    ))

            # Step 1: Extract raw content based on source type
            # Extractor progress is scaled to 0-50% range via sync_progress_callback above
            extractor = self._get_extractor(source_type, sync_progress_callback)
            raw_content = await extractor.extract(source)

            # Step 2: Normalize and structure the recipe using AI (50-70% range)
            # For photos, the extractor already returns structured data, skip normalization
            if source_type == SourceType.PHOTO:
                # Photo extractor returns structured recipe directly
                normalized_data = raw_content

                if job_id:
                    await self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        55,
                        "Recipe data extracted"
                    )
                elif progress_callback:
                    # Only use progress_callback if no job_id (backward compatibility)
                    progress_callback(55, "Recipe data extracted")
            else:
                # Other extractors return raw text that needs normalization
                if job_id:
                    await self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        55,
                        "Normalizing recipe data"
                    )
                elif progress_callback:
                    # Only use progress_callback if no job_id (backward compatibility)
                    progress_callback(55, "Normalizing recipe data")

                normalized_data = await self.openai_service.normalize_recipe(
                    raw_content["text"],
                    source_type.value
                )

            # Step 3: Prepare recipe for database (70% range)
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.PROCESSING,
                    70,
                    "Preparing recipe data"
                )
            elif progress_callback:
                # Only use progress_callback if no job_id (backward compatibility)
                progress_callback(70, "Preparing recipe data")

            # Get source URLs (could be single or multiple)
            # For backwards compatibility with non-photo sources
            source_url = raw_content.get("source_url") if "source_url" in raw_content else None
            source_urls = raw_content.get("source_urls", [source_url] if source_url else [])

            # Determine initial image_url (from extraction source)
            initial_image_url = source_urls[0] if source_urls else None

            # Step 4: Generate AI image for non-webpage sources (75-85% range)
            # LINK sources with webpages already have images from scraping
            # Check if this is NOT a LINK type (which would be handled by LinkExtractor)
            if source_type != SourceType.LINK:
                if job_id:
                    await self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        75,
                        "Generating AI image"
                    )
                elif progress_callback:
                    progress_callback(75, "Generating AI image")

                # Generate image synchronously (recipe_id will be auto-generated)
                generated_image_url = await self.flux_service.generate_recipe_image(
                    normalized_data,
                    user_id
                )

                # Use generated image if successful, otherwise keep source image
                if generated_image_url:
                    initial_image_url = generated_image_url
                    logger.info(f"Generated AI image for recipe: {generated_image_url}")
                else:
                    logger.warning("Image generation failed, using source image if available")

            recipe_data = {
                "title": normalized_data["title"],
                "description": normalized_data.get("description"),
                "ingredients": normalized_data.get("ingredients", []),
                "instructions": normalized_data.get("instructions", []),
                "servings": normalized_data.get("servings"),
                "difficulty": normalized_data.get("difficulty"),
                "tags": normalized_data.get("tags", []),
                "categories": normalized_data.get("categories", []),
                "prep_time_minutes": normalized_data.get("prep_time_minutes"),
                "cook_time_minutes": normalized_data.get("cook_time_minutes"),
                "total_time_minutes": normalized_data.get("total_time_minutes"),
                "source_type": source_type.value,
                "source_url": source_url,  # Keep for backward compatibility
                "image_url": initial_image_url,  # Generated or source image
                "created_by": user_id,
                "is_public": True  # Default to public as specified
            }

            # Create recipe in database (with generated image already included)
            recipe = await self.recipe_repo.create(recipe_data)

            # Create contributor record
            self.supabase.table("recipe_contributors").insert({
                "recipe_id": recipe["id"],
                "user_id": user_id,
                "contribution_type": "creator",
                "order": 0
            }).execute()

            # Log extraction stats if available (from photo extraction)
            if "_extraction_stats" in normalized_data:
                stats = normalized_data["_extraction_stats"]
                logger.info(
                    f"Extraction stats - Model: {stats.get('model')}, "
                    f"Tokens: {stats.get('total_tokens')}, "
                    f"Cost: ${stats.get('estimated_cost_usd', 0):.4f}"
                )

            # Update job status to completed
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.COMPLETED,
                    100,
                    "Extraction complete",
                    recipe_id=recipe["id"]
                )
            elif progress_callback:
                # Only use progress_callback if no job_id (backward compatibility)
                progress_callback(100, "Recipe created successfully")

            logger.info(f"Successfully created recipe {recipe['id']} from {source_type.value}")

            return recipe

        except Exception as e:
            logger.error(f"Error in extraction process: {str(e)}")

            # Update job status to failed
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.FAILED,
                    0,
                    "Extraction failed",
                    error_message=str(e)
                )

            raise

    def _get_extractor(self, source_type: SourceType, progress_callback=None):
        """Get appropriate extractor for source type"""
        extractors = {
            SourceType.VIDEO: VideoExtractor,
            SourceType.PHOTO: PhotoExtractor,
            SourceType.VOICE: VoiceExtractor,
            SourceType.PASTE: PasteExtractor,
            SourceType.LINK: LinkExtractor,
        }

        extractor_class = extractors.get(source_type)
        if not extractor_class:
            raise ValueError(f"Unsupported source type: {source_type}")

        return extractor_class(progress_callback)

    async def _update_job_status(
        self,
        job_id: str,
        status: ExtractionStatus,
        progress: int,
        step: str,
        recipe_id: Optional[str] = None,
        error_message: Optional[str] = None,
        existing_recipe_id: Optional[str] = None
    ):
        """Update extraction job status"""
        try:
            update_data = {
                "status": status.value,
                "progress_percentage": progress,
                "current_step": step
            }

            if recipe_id:
                update_data["recipe_id"] = recipe_id

            if error_message:
                update_data["error_message"] = error_message

            if existing_recipe_id:
                update_data["existing_recipe_id"] = existing_recipe_id

            # Run Supabase update in thread pool to avoid blocking event loop
            await asyncio.to_thread(
                lambda: self.supabase.table("extraction_jobs")
                    .update(update_data)
                    .eq("id", job_id)
                    .execute()
            )

            # Broadcast event to SSE subscribers
            try:
                broadcaster = get_event_broadcaster()
                event_data = {
                    "id": job_id,
                    "status": status.value,
                    "progress_percentage": progress,
                    "current_step": step
                }
                if recipe_id:
                    event_data["recipe_id"] = recipe_id
                if error_message:
                    event_data["error_message"] = error_message
                if existing_recipe_id:
                    event_data["existing_recipe_id"] = existing_recipe_id

                await broadcaster.publish(job_id, event_data)
                logger.debug(f"Broadcasted event for job {job_id}: {event_data}")
            except Exception as broadcast_error:
                # Don't fail the update if broadcast fails
                logger.error(f"Error broadcasting event: {str(broadcast_error)}")

        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")

    async def create_extraction_job(
        self,
        user_id: str,
        source_type: SourceType,
        source_url: Optional[str] = None,
        source_urls: Optional[List[str]] = None
    ) -> str:
        """Create a new extraction job and return job ID"""
        try:
            # Prepare source URLs array
            urls_array = source_urls if source_urls else ([source_url] if source_url else [])

            result = self.supabase.table("extraction_jobs").insert({
                "user_id": user_id,
                "source_type": source_type.value,
                "source_url": source_url or (urls_array[0] if urls_array else None),  # First URL for backward compatibility
                "source_urls": urls_array,  # Array of all URLs
                "status": ExtractionStatus.PENDING.value,
                "progress_percentage": 0
            }).execute()

            return result.data[0]["id"]

        except Exception as e:
            logger.error(f"Error creating extraction job: {str(e)}")
            raise

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get extraction job status"""
        try:
            result = self.supabase.table("extraction_jobs")\
                .select("*")\
                .eq("id", job_id)\
                .execute()

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            raise

    async def extract_recipe(
        self,
        user_id: str,
        source_type: SourceType,
        source: Union[str, List[str]],
        job_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Extract recipe from source(s) and create a DRAFT recipe.

        This creates a draft recipe (is_draft=true) that the user can preview.
        The user must explicitly save to publish the recipe and add to collection.

        For video URLs, this checks for duplicates first and returns the existing
        recipe_id if found (no new draft created).

        Args:
            user_id: User performing the extraction
            source_type: Type of source
            source: Source URL/content or list of URLs
            job_id: Optional extraction job ID for tracking
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with job_id, status, recipe_id (always set - draft or existing)
        """
        try:
            # Update job status if provided
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.PROCESSING,
                    0,
                    "Starting extraction"
                )

            # Check for duplicates based on source type
            if isinstance(source, str):
                is_video_url = (
                    source_type == SourceType.VIDEO or
                    (source_type == SourceType.LINK and VideoURLParser.is_video_url(source))
                )
                is_regular_url = (
                    source_type == SourceType.LINK and not VideoURLParser.is_video_url(source)
                )

                duplicate_check = None

                # Check video duplicates for video URLs
                if is_video_url:
                    duplicate_check = await self._check_video_duplicate(source)
                    if duplicate_check:
                        logger.info(f"Video duplicate found: {duplicate_check['recipe_id']}")

                # Check URL duplicates for regular URLs
                elif is_regular_url:
                    duplicate_check = await self._check_url_duplicate(source)
                    if duplicate_check:
                        logger.info(f"URL duplicate found: {duplicate_check['recipe_id']}")

                # Return early if duplicate found
                if duplicate_check:
                    existing_recipe_id = duplicate_check["recipe_id"]
                    if job_id:
                        await self._update_job_status(
                            job_id,
                            ExtractionStatus.COMPLETED,
                            100,
                            "Recipe already exists",
                            existing_recipe_id=existing_recipe_id
                        )

                    return {
                        "job_id": None,  # No job needed for duplicates
                        "status": "duplicate",
                        "recipe_id": existing_recipe_id
                    }

            # Create progress callback that updates database if job_id is provided
            # Scale extractor progress (0-100%) to 0-50% range so service steps can use 50-100%
            def sync_progress_callback(percentage: int, step: str):
                """Synchronous wrapper for progress updates with scaling"""
                # Scale extractor's 0-100% to 0-50% range
                scaled_percentage = int(percentage * 0.5)
                if progress_callback:
                    progress_callback(scaled_percentage, step)
                if job_id:
                    asyncio.create_task(self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        scaled_percentage,
                        step
                    ))

            # Step 1: Extract raw content based on source type
            # Extractor progress is scaled to 0-50% range via sync_progress_callback above
            extractor = self._get_extractor(source_type, sync_progress_callback)
            raw_content = await extractor.extract(source)

            # Step 2: Normalize and structure the recipe using AI (50-70% range)
            if source_type == SourceType.PHOTO:
                normalized_data = raw_content
                if job_id:
                    await self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        55,
                        "Recipe data extracted"
                    )
            else:
                if job_id:
                    await self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        55,
                        "Normalizing recipe data"
                    )
                normalized_data = await self.openai_service.normalize_recipe(
                    raw_content["text"],
                    source_type.value
                )

            # Step 3: Prepare extraction data (70% range)
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.PROCESSING,
                    70,
                    "Preparing recipe data"
                )

            # Get source URLs
            source_url = raw_content.get("source_url") if "source_url" in raw_content else None
            source_urls = raw_content.get("source_urls", [source_url] if source_url else [])
            initial_image_url = source_urls[0] if source_urls else None

            # Step 4: Handle image based on source type (75-85% range)
            # For LINK type, check detected_type to determine handling
            detected_type = raw_content.get("detected_type")
            is_video_content = source_type == SourceType.VIDEO or detected_type == "video"
            is_url_content = detected_type == "url"

            if is_video_content:
                # For video, use thumbnail from metadata
                initial_image_url = raw_content.get("thumbnail_url") or initial_image_url
            elif is_url_content:
                # For URL/webpage, use extracted image from page
                initial_image_url = raw_content.get("image_url") or initial_image_url
            else:
                # For other types (photo, voice, paste), generate AI image
                if job_id:
                    await self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        75,
                        "Generating AI image"
                    )

                generated_image_url = await self.flux_service.generate_recipe_image(
                    normalized_data,
                    user_id
                )
                if generated_image_url:
                    initial_image_url = generated_image_url

            # Build extraction data (recipe-like structure)
            extraction_data = {
                "title": normalized_data["title"],
                "description": normalized_data.get("description"),
                "ingredients": normalized_data.get("ingredients", []),
                "instructions": normalized_data.get("instructions", []),
                "servings": normalized_data.get("servings"),
                "difficulty": normalized_data.get("difficulty"),
                "tags": normalized_data.get("tags", []),
                "categories": normalized_data.get("categories", []),
                "prep_time_minutes": normalized_data.get("prep_time_minutes"),
                "cook_time_minutes": normalized_data.get("cook_time_minutes"),
                "total_time_minutes": normalized_data.get("total_time_minutes"),
                "source_url": source_url,
                "image_url": initial_image_url,
            }

            # Build video metadata if applicable (for VIDEO type or LINK that detected video)
            video_metadata = None
            if is_video_content:
                video_metadata = self._build_video_metadata(raw_content, source)

            # Log extraction stats if available
            if "_extraction_stats" in normalized_data:
                stats = normalized_data["_extraction_stats"]
                logger.info(
                    f"Extraction stats - Model: {stats.get('model')}, "
                    f"Tokens: {stats.get('total_tokens')}, "
                    f"Cost: ${stats.get('estimated_cost_usd', 0):.4f}"
                )

            # Step 5: Create DRAFT recipe (90% range)
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.PROCESSING,
                    90,
                    "Creating draft recipe"
                )

            result = await self.recipe_save_service.create_draft_recipe(
                user_id=user_id,
                source_type=source_type,
                extracted_data=extraction_data,
                video_metadata=video_metadata,
                source_url=source_url,
                job_id=job_id
            )

            recipe_id = result["recipe_id"]

            # Update job status to completed
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.COMPLETED,
                    100,
                    "Extraction complete",
                    recipe_id=recipe_id
                )

            logger.info(f"Successfully created draft recipe {recipe_id} from {source_type.value}")

            return {
                "job_id": job_id,
                "status": "completed",
                "recipe_id": recipe_id
            }

        except NotARecipeError as e:
            logger.info(f"Content not a recipe: {e.message}")
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.NOT_A_RECIPE,
                    100,
                    "Content analysis complete",
                    error_message=e.message
                )
            return {
                "job_id": job_id,
                "status": "not_a_recipe",
                "recipe_id": None
            }

        except WebsiteBlockedError as e:
            logger.info(f"Website blocks extraction: {e.url}")
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.WEBSITE_BLOCKED,
                    100,
                    "Website blocks automated extraction",
                    error_message=e.message
                )
            return {
                "job_id": job_id,
                "status": "website_blocked",
                "recipe_id": None
            }

        except Exception as e:
            logger.error(f"Error in extraction process: {str(e)}")
            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.FAILED,
                    0,
                    "Extraction failed",
                    error_message=str(e)
                )
            raise

    async def _check_video_duplicate(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Check if a video URL has already been extracted.

        Args:
            url: Video URL to check

        Returns:
            Dict with recipe_id, is_public, created_by if duplicate found, None otherwise
        """
        parsed = VideoURLParser.parse(url)
        if not parsed:
            return None

        return await self.video_source_repo.check_duplicate(
            platform=parsed.platform.value,
            platform_video_id=parsed.video_id
        )

    async def _check_url_duplicate(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Check if a URL has already been extracted as a recipe.

        Args:
            url: URL to check

        Returns:
            Dict with recipe_id, is_public, created_by if duplicate found, None otherwise
        """
        return await self.recipe_repo.find_by_source_url(url)

    def _build_video_metadata(
        self,
        raw_content: Dict[str, Any],
        source_url: str
    ) -> Dict[str, Any]:
        """
        Build video metadata structure from extraction result.

        Args:
            raw_content: Raw content from video extractor
            source_url: Original source URL

        Returns:
            Video metadata dict
        """
        parsed = VideoURLParser.parse(source_url)

        metadata = {
            "platform": parsed.platform.value if parsed else None,
            "platform_video_id": parsed.video_id if parsed else None,
            "original_url": source_url,
            "canonical_url": raw_content.get("webpage_url"),
            "title": raw_content.get("video_title"),
            "description": raw_content.get("description"),
            "duration_seconds": raw_content.get("duration"),
            "thumbnail_url": raw_content.get("thumbnail_url"),
            "view_count": raw_content.get("view_count"),
            "like_count": raw_content.get("like_count"),
            "upload_date": raw_content.get("upload_date"),
            "creator": {
                "platform_user_id": raw_content.get("uploader_id") or raw_content.get("channel_id"),
                "platform_username": raw_content.get("uploader") or raw_content.get("channel"),
                "display_name": raw_content.get("uploader"),
                "profile_url": raw_content.get("channel_url")
            },
            "raw_metadata": raw_content.get("raw_metadata")
        }

        return metadata

