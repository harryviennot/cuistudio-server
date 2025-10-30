"""
Recipe extraction endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, File, UploadFile, Request
from supabase import Client
from typing import List
import logging

from app.core.database import get_supabase_client, get_supabase_admin_client, get_supabase_user_client
from app.core.security import get_current_user
from app.services.extraction_service import ExtractionService
from app.services.upload_service import UploadService
from app.api.v1.schemas.extraction import (
    ExtractionSubmitRequest,
    ExtractionJobResponse,
    ImageExtractionResponse
)
from app.api.v1.schemas.upload import MAX_IMAGES_PER_EXTRACTION
from app.domain.enums import SourceType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/extraction", tags=["Extraction"])


@router.post("/submit", response_model=ExtractionJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_extraction(
    extraction_request: ExtractionSubmitRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    user_client: Client = Depends(get_supabase_user_client),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    Submit content for recipe extraction.
    Returns a job ID for tracking progress.
    """
    try:
        # Use user_client for job creation (respects RLS)
        extraction_service = ExtractionService(user_client)

        # Create extraction job
        job_id = await extraction_service.create_extraction_job(
            current_user["id"],
            extraction_request.source_type,
            extraction_request.source_url
        )

        # Determine source based on type
        source = extraction_request.source_url or extraction_request.text_content or extraction_request.file_url

        if not source:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source URL, text content, or file URL is required"
            )

        # Run extraction in background (use admin_client for background tasks)
        admin_extraction_service = ExtractionService(admin_client)
        background_tasks.add_task(
            admin_extraction_service.extract_and_create_recipe,
            current_user["id"],
            extraction_request.source_type,
            source,
            job_id
        )

        # Get and return job status
        job = await extraction_service.get_job_status(job_id)

        return ExtractionJobResponse(**job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting extraction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit extraction: {str(e)}"
        )


@router.post("/submit-images", response_model=ImageExtractionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_image_extraction(
    request: Request,
    files: List[UploadFile] = File(..., description=f"Recipe images (max {MAX_IMAGES_PER_EXTRACTION})"),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
    user_client: Client = Depends(get_supabase_user_client),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    Upload images and submit for recipe extraction in one step.

    This endpoint combines image upload and extraction submission for better UX.
    Accepts 1-3 images and returns a job ID for tracking extraction progress.
    """
    try:
        # Validate number of images
        if len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one image is required"
            )

        if len(files) > MAX_IMAGES_PER_EXTRACTION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {MAX_IMAGES_PER_EXTRACTION} images allowed per extraction"
            )

        # Step 1: Upload all images
        upload_service = UploadService(admin_client)
        uploaded_images = await upload_service.upload_images(files, current_user["id"])

        # Extract URLs from uploaded images
        image_urls = [img["url"] for img in uploaded_images]

        # Step 2: Create extraction job (use user_client for RLS)
        extraction_service = ExtractionService(user_client)
        job_id = await extraction_service.create_extraction_job(
            current_user["id"],
            SourceType.PHOTO,
            source_urls=image_urls
        )

        # Step 3: Run extraction in background (use admin_client for background tasks)
        admin_extraction_service = ExtractionService(admin_client)
        background_tasks.add_task(
            admin_extraction_service.extract_and_create_recipe,
            current_user["id"],
            SourceType.PHOTO,
            image_urls,  # Pass list of URLs
            job_id
        )

        return ImageExtractionResponse(
            job_id=job_id,
            message=f"Recipe extraction started with {len(files)} image(s). Poll /extraction/jobs/{job_id} for status.",
            image_count=len(files)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting image extraction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit image extraction: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=ExtractionJobResponse)
async def get_extraction_job(
    job_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    user_client: Client = Depends(get_supabase_user_client)
):
    """Get extraction job status"""
    try:
        extraction_service = ExtractionService(user_client)

        job = await extraction_service.get_job_status(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Check ownership
        if job["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this job"
            )

        return ExtractionJobResponse(**job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting extraction job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get extraction job: {str(e)}"
        )
