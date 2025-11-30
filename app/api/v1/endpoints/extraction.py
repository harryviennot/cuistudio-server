"""
Recipe extraction endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, File, UploadFile, Request
from sse_starlette.sse import EventSourceResponse
from supabase import Client
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
import asyncio
import json
import time

from app.core.database import get_supabase_client, get_supabase_admin_client, get_supabase_user_client
from app.core.security import get_current_user
from app.core.events import get_event_broadcaster
from app.services.extraction_service import ExtractionService
from app.services.upload_service import UploadService
from app.services.openai_service import OpenAIService
from app.services.extractors.photo_extractor import PhotoExtractor
from app.api.v1.schemas.extraction import (
    ExtractionSubmitRequest,
    ExtractionJobResponse,
    ImageExtractionResponse
)
from app.api.v1.schemas.common import MessageResponse
from app.api.v1.schemas.upload import MAX_IMAGES_PER_EXTRACTION
from app.domain.enums import SourceType, ExtractionStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/extraction", tags=["Extraction"])


# Benchmark schemas
class BenchmarkRequest(BaseModel):
    image_path: str  # Local file path to image


class BenchmarkResult(BaseModel):
    image_path: str
    ocr_text: str
    with_image: Dict[str, Any]
    ocr_only: Dict[str, Any]


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

    This endpoint extracts recipe data WITHOUT saving to the database.
    The extracted data is stored in the job and returned when complete.
    Use POST /recipes/save to persist the recipe after preview.

    For video URLs (TikTok, YouTube Shorts, Instagram Reels), duplicate
    detection is performed first. If the video was already extracted,
    the existing recipe data is returned with existing_recipe_id set.

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
        # Use the new extract_recipe method that doesn't save to DB
        admin_extraction_service = ExtractionService(admin_client)
        background_tasks.add_task(
            admin_extraction_service.extract_recipe,
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
        # Use extract_recipe to only extract without saving - user must confirm via /recipes/save
        admin_extraction_service = ExtractionService(admin_client)
        background_tasks.add_task(
            admin_extraction_service.extract_recipe,
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


@router.delete("/jobs/{job_id}", response_model=MessageResponse)
async def cancel_extraction_job(
    job_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    user_client: Client = Depends(get_supabase_user_client)
):
    """
    Cancel an extraction job.

    Only jobs with status 'pending' or 'processing' can be cancelled.
    Cancelling a job will prevent the recipe from being created, but the
    background extraction process may continue until it checks the status.
    """
    try:
        extraction_service = ExtractionService(user_client)

        result = await extraction_service.cancel_extraction_job(
            job_id,
            current_user["id"]
        )

        return MessageResponse(**result)

    except ValueError as e:
        # Map ValueError to appropriate HTTP errors
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "permission" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        else:
            # Cannot cancel (wrong status)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling extraction job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel extraction job: {str(e)}"
        )


@router.get("/jobs/{job_id}/stream")
async def stream_extraction_job(
    job_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    user_client: Client = Depends(get_supabase_user_client)
):
    """
    Stream extraction job status updates via Server-Sent Events (SSE).

    This endpoint provides real-time progress updates, reducing the need for polling.
    The connection automatically closes when the job completes or fails.

    Event format:
    {
        "id": "job_id",
        "status": "processing" | "completed" | "failed",
        "progress_percentage": 0-100,
        "current_step": "Step description",
        "recipe_id": "recipe_id" (when completed),
        "error_message": "error" (when failed)
    }
    """
    try:
        extraction_service = ExtractionService(user_client)

        # Verify job exists and user has access
        job = await extraction_service.get_job_status(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        if job["user_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this job"
            )

        # Get event broadcaster
        broadcaster = get_event_broadcaster()

        async def event_stream():
            """Generate Server-Sent Events for job updates"""
            try:
                # Send initial state immediately
                initial_data = {
                    "id": job["id"],
                    "status": job["status"],
                    "progress_percentage": job.get("progress_percentage", 0),
                    "current_step": job.get("current_step", ""),
                    "recipe_id": job.get("recipe_id"),
                    "error_message": job.get("error_message")
                }
                yield {
                    "event": "job_update",
                    "data": json.dumps(initial_data)
                }

                # Send an immediate heartbeat to keep connection alive
                await asyncio.sleep(0.1)
                yield {"comment": "connected"}

                # If job is already complete, close immediately
                if job["status"] in [ExtractionStatus.COMPLETED.value, ExtractionStatus.FAILED.value]:
                    logger.info(f"Job {job_id} already {job['status']}, closing SSE connection")
                    return

                # Subscribe to real-time updates with timeout
                async with broadcaster.subscribe(job_id) as event_generator:
                    # Set a timeout for waiting for events (30 seconds)
                    while True:
                        try:
                            # Wait for next event with timeout
                            event_data = await asyncio.wait_for(
                                event_generator.__anext__(),
                                timeout=30.0
                            )

                            # Check if client disconnected
                            if await request.is_disconnected():
                                logger.info(f"Client disconnected from SSE stream for job {job_id}")
                                break

                            # Send update event (serialize to JSON)
                            yield {
                                "event": "job_update",
                                "data": json.dumps(event_data)
                            }

                            # Close connection if job is complete
                            if event_data.get("status") in [ExtractionStatus.COMPLETED.value, ExtractionStatus.FAILED.value]:
                                logger.info(f"Job {job_id} {event_data['status']}, closing SSE connection")
                                break

                        except asyncio.TimeoutError:
                            # Send keep-alive ping every 30 seconds
                            yield {"comment": "keep-alive"}
                        except StopAsyncIteration:
                            # No more events
                            break

            except asyncio.CancelledError:
                logger.info(f"SSE stream cancelled for job {job_id}")
            except Exception as e:
                logger.error(f"Error in SSE stream for job {job_id}: {e}")
                # Send error event
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Stream error occurred"})
                }

        return EventSourceResponse(event_stream())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting SSE stream: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start event stream: {str(e)}"
        )


# =============================================================================
# BENCHMARK ENDPOINT (Temporary - No Auth Required)
# =============================================================================

@router.post("/benchmark", response_model=BenchmarkResult)
async def benchmark_extraction(
    request: BenchmarkRequest
):
    """
    Benchmark endpoint to compare image extraction methods.

    Runs both extraction methods on the same image:
    1. With Image: OCR + GPT-4o-mini with image (current production method)
    2. OCR-Only: OCR + GPT-4o-mini with only OCR text (no image)

    NO AUTHENTICATION REQUIRED - This is temporary for benchmarking.
    Remove this endpoint after benchmarking is complete.
    """
    import os
    from PIL import Image
    import io

    image_path = request.image_path

    # Validate file exists
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image file not found: {image_path}"
        )

    try:
        # Initialize services
        openai_service = OpenAIService()
        photo_extractor = PhotoExtractor()

        # Step 1: Run OCR (shared between both methods)
        logger.info(f"Running OCR on {image_path}")
        ocr_start = time.time()
        ocr_text = await photo_extractor._run_ocr(image_path)
        ocr_time = time.time() - ocr_start
        logger.info(f"OCR completed in {ocr_time:.2f}s, extracted {len(ocr_text)} chars")

        # Step 2: Method A - With Image (current production method)
        logger.info("Running extraction WITH image...")
        with_image_start = time.time()
        try:
            with_image_result = await openai_service.extract_recipe_from_image_with_ocr(
                image_path,
                ocr_text
            )
            with_image_time = time.time() - with_image_start
            with_image_result["_benchmark"] = {
                "extraction_time_seconds": with_image_time,
                "ocr_time_seconds": ocr_time,
                "total_time_seconds": ocr_time + with_image_time
            }
            with_image_error = None
        except Exception as e:
            with_image_time = time.time() - with_image_start
            with_image_result = {
                "_benchmark": {
                    "extraction_time_seconds": with_image_time,
                    "ocr_time_seconds": ocr_time,
                    "total_time_seconds": ocr_time + with_image_time
                }
            }
            with_image_error = str(e)
            logger.error(f"With-image extraction failed: {e}")

        # Step 3: Method B - OCR Only (no image)
        logger.info("Running extraction OCR-ONLY...")
        ocr_only_start = time.time()
        try:
            ocr_only_result = await openai_service.extract_recipe_from_ocr_text_only(ocr_text)
            ocr_only_time = time.time() - ocr_only_start
            ocr_only_result["_benchmark"] = {
                "extraction_time_seconds": ocr_only_time,
                "ocr_time_seconds": ocr_time,
                "total_time_seconds": ocr_time + ocr_only_time
            }
            ocr_only_error = None
        except Exception as e:
            ocr_only_time = time.time() - ocr_only_start
            ocr_only_result = {
                "_benchmark": {
                    "extraction_time_seconds": ocr_only_time,
                    "ocr_time_seconds": ocr_time,
                    "total_time_seconds": ocr_time + ocr_only_time
                }
            }
            ocr_only_error = str(e)
            logger.error(f"OCR-only extraction failed: {e}")

        # Add errors if any
        if with_image_error:
            with_image_result["error"] = with_image_error
        if ocr_only_error:
            ocr_only_result["error"] = ocr_only_error

        logger.info(f"Benchmark complete for {image_path}")
        logger.info(f"  With image: {with_image_time:.2f}s")
        logger.info(f"  OCR only: {ocr_only_time:.2f}s")

        return BenchmarkResult(
            image_path=image_path,
            ocr_text=ocr_text,
            with_image=with_image_result,
            ocr_only=ocr_only_result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Benchmark error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark failed: {str(e)}"
        )
