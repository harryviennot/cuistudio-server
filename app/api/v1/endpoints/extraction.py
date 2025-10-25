"""
Recipe extraction endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from supabase import Client
import logging

from app.core.database import get_supabase_client
from app.core.security import get_current_user
from app.services.extraction_service import ExtractionService
from app.api.v1.schemas.extraction import (
    ExtractionSubmitRequest,
    ExtractionJobResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/extraction", tags=["Extraction"])


@router.post("/submit", response_model=ExtractionJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_extraction(
    request: ExtractionSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Submit content for recipe extraction.
    Returns a job ID for tracking progress.
    """
    try:
        extraction_service = ExtractionService(supabase)

        # Create extraction job
        job_id = await extraction_service.create_extraction_job(
            current_user["id"],
            request.source_type,
            request.source_url
        )

        # Determine source based on type
        source = request.source_url or request.text_content or request.file_url

        if not source:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source URL, text content, or file URL is required"
            )

        # Run extraction in background
        background_tasks.add_task(
            extraction_service.extract_and_create_recipe,
            current_user["id"],
            request.source_type,
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


@router.get("/jobs/{job_id}", response_model=ExtractionJobResponse)
async def get_extraction_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get extraction job status"""
    try:
        extraction_service = ExtractionService(supabase)

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
