"""
Extraction orchestrator service
Coordinates extraction from different sources and normalization
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Union, List
from supabase import Client

from app.domain.enums import SourceType, ExtractionStatus
from app.services.extractors.video_extractor import VideoExtractor
from app.services.extractors.photo_extractor import PhotoExtractor
from app.services.extractors.voice_extractor import VoiceExtractor
from app.services.extractors.url_extractor import URLExtractor
from app.services.extractors.paste_extractor import PasteExtractor
from app.services.openai_service import OpenAIService
from app.repositories.recipe_repository import RecipeRepository

logger = logging.getLogger(__name__)


class ExtractionService:
    """Orchestrates recipe extraction from various sources"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.openai_service = OpenAIService()
        self.recipe_repo = RecipeRepository(supabase)

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

            # Step 1: Extract raw content based on source type
            if progress_callback:
                progress_callback(10, "Extracting content from source")

            extractor = self._get_extractor(source_type, progress_callback)
            raw_content = await extractor.extract(source)

            # Step 2: Normalize and structure the recipe using AI
            # For photos, the extractor already returns structured data, skip normalization
            if source_type == SourceType.PHOTO:
                # Photo extractor returns structured recipe directly
                normalized_data = raw_content

                if progress_callback:
                    progress_callback(60, "Recipe data extracted")

                if job_id:
                    await self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        60,
                        "Recipe data extracted"
                    )
            else:
                # Other extractors return raw text that needs normalization
                if progress_callback:
                    progress_callback(60, "Normalizing recipe data")

                if job_id:
                    await self._update_job_status(
                        job_id,
                        ExtractionStatus.PROCESSING,
                        60,
                        "Normalizing recipe data"
                    )

                normalized_data = await self.openai_service.normalize_recipe(
                    raw_content["text"],
                    source_type.value
                )

            # Step 3: Prepare recipe for database
            if progress_callback:
                progress_callback(80, "Saving recipe")

            if job_id:
                await self._update_job_status(
                    job_id,
                    ExtractionStatus.PROCESSING,
                    80,
                    "Saving recipe"
                )

            # Get source URLs (could be single or multiple)
            # For backwards compatibility with non-photo sources
            source_url = raw_content.get("source_url") if "source_url" in raw_content else None
            source_urls = raw_content.get("source_urls", [source_url] if source_url else [])

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
                "created_by": user_id,
                "is_public": True  # Default to public as specified
            }

            # Create recipe in database
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

            if progress_callback:
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
            SourceType.URL: URLExtractor,
            SourceType.PASTE: PasteExtractor
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
        error_message: Optional[str] = None
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

            # Run Supabase update in thread pool to avoid blocking event loop
            await asyncio.to_thread(
                lambda: self.supabase.table("extraction_jobs")
                    .update(update_data)
                    .eq("id", job_id)
                    .execute()
            )

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
