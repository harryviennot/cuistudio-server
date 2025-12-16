"""
Image upload endpoints
"""
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from supabase import Client
from typing import List
import logging

from app.core.database import get_supabase_admin_client
from app.core.security import get_current_user
from app.services.upload_service import UploadService, ALLOWED_BUCKETS, DEFAULT_STORAGE_BUCKET
from app.api.v1.schemas.upload import (
    ImageUploadResponse,
    MultipleImageUploadResponse,
    VideoUploadResponse,
    MAX_IMAGES_PER_EXTRACTION,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])


# ============================================================================
# SINGLE IMAGE UPLOAD
# ============================================================================

@router.post(
    "/image",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Single Image",
    description="Upload a single image to Supabase Storage for recipe extraction",
    responses={
        201: {
            "description": "Image uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "url": "https://project.supabase.co/storage/v1/object/public/recipe-images/user-id/uuid.jpg",
                        "path": "user-id/uuid.jpg",
                        "size": 1024000,
                        "content_type": "image/jpeg"
                    }
                }
            }
        },
        400: {"description": "Invalid file type or size"},
        401: {"description": "Not authenticated"},
        413: {"description": "File too large"}
    }
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload (jpg, png, heic, webp)"),
    bucket: str = Form(DEFAULT_STORAGE_BUCKET, description="Target storage bucket (recipe-images or cooking-events)"),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    ## Upload Single Image

    Uploads a single image to Supabase Storage and returns the public URL.

    **Allowed File Types:**
    - image/jpeg (.jpg, .jpeg)
    - image/png (.png)
    - image/heic (.heic)
    - image/webp (.webp)

    **File Size Limit:** 50MB

    **Storage Buckets:**
    - `recipe-images` (default): For recipe extraction images
    - `cooking-events`: For cooking session photos

    **Storage Structure:**
    - Path: `{user_id}/{uuid}.{extension}`

    **Authentication:**
    - Requires valid JWT access token (Bearer token)
    - Works with both anonymous and authenticated users

    **Use Case:**
    - Upload a single recipe image before extraction
    - Upload a cooking session photo
    - Get public URL to pass to extraction endpoint

    **Next Steps:**
    After uploading, use the returned URL with:
    - `POST /extraction/submit` with `file_url` parameter
    - Or use `POST /extraction/submit-images` to upload and extract in one step
    """
    # Validate bucket is allowed
    if bucket not in ALLOWED_BUCKETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid bucket '{bucket}'. Allowed buckets: {', '.join(ALLOWED_BUCKETS)}"
        )

    upload_service = UploadService(supabase)

    try:
        result = await upload_service.upload_image(file, current_user["id"], bucket=bucket)
        return ImageUploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while uploading the image"
        )


# ============================================================================
# MULTIPLE IMAGE UPLOAD
# ============================================================================

@router.post(
    "/images",
    response_model=MultipleImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Multiple Images",
    description=f"Upload multiple images (up to {MAX_IMAGES_PER_EXTRACTION}) to Supabase Storage for recipe extraction",
    responses={
        201: {
            "description": "Images uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "images": [
                            {
                                "url": "https://project.supabase.co/storage/v1/object/public/recipe-images/user-id/uuid1.jpg",
                                "path": "user-id/uuid1.jpg",
                                "size": 1024000,
                                "content_type": "image/jpeg"
                            },
                            {
                                "url": "https://project.supabase.co/storage/v1/object/public/recipe-images/user-id/uuid2.jpg",
                                "path": "user-id/uuid2.jpg",
                                "size": 2048000,
                                "content_type": "image/png"
                            }
                        ],
                        "total_count": 2,
                        "total_size": 3072000
                    }
                }
            }
        },
        400: {"description": "Invalid file type, size, or too many files"},
        401: {"description": "Not authenticated"},
        413: {"description": "One or more files too large"}
    }
)
async def upload_images(
    files: List[UploadFile] = File(..., description=f"List of image files (max {MAX_IMAGES_PER_EXTRACTION})"),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    ## Upload Multiple Images

    Uploads multiple images to Supabase Storage for multi-image recipe extraction.

    **Limits:**
    - Minimum: 1 image
    - Maximum: 5 images per request
    - Max file size: 50MB per image

    **Allowed File Types:**
    - image/jpeg (.jpg, .jpeg)
    - image/png (.png)
    - image/heic (.heic)
    - image/webp (.webp)

    **Storage Structure:**
    - All images stored in `recipe-images` bucket
    - Each image has unique path: `{user_id}/{uuid}.{extension}`

    **Use Cases:**
    - Upload multiple angles of a recipe
    - Upload ingredient list + cooking steps separately
    - Upload multiple pages of a cookbook recipe

    **Authentication:**
    - Requires valid JWT access token (Bearer token)
    - Works with both anonymous and authenticated users

    **Batch Processing:**
    - All files are validated before any uploads
    - If one file fails validation, entire request fails
    - If upload fails mid-batch, already uploaded files remain in storage

    **Next Steps:**
    After uploading, use the returned URLs with:
    - `POST /extraction/submit` with `file_urls` parameter (array)
    - Or use `POST /extraction/submit-images` to upload and extract in one step
    """
    upload_service = UploadService(supabase)

    try:
        results = await upload_service.upload_images(files, current_user["id"])

        # Calculate totals
        total_size = sum(r["size"] for r in results)

        return MultipleImageUploadResponse(
            images=[ImageUploadResponse(**r) for r in results],
            total_count=len(results),
            total_size=total_size
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while uploading images"
        )


# ============================================================================
# VIDEO UPLOAD (for Instagram client-side download)
# ============================================================================

@router.post(
    "/video",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Video for Extraction",
    description="Upload a video file for recipe extraction (used for Instagram client-side downloads)",
    responses={
        201: {
            "description": "Video uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "path": "job-id/uuid.mp4",
                        "size": 52428800,
                        "content_type": "video/mp4"
                    }
                }
            }
        },
        400: {"description": "Invalid file type or missing job_id"},
        401: {"description": "Not authenticated"},
        413: {"description": "Video too large"}
    }
)
async def upload_video(
    file: UploadFile = File(..., description="Video file to upload (mp4, mov)"),
    job_id: str = Form(..., description="Extraction job ID"),
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    ## Upload Video for Extraction

    Uploads a video file to server's local filesystem for recipe extraction.
    Used when the mobile client downloads an Instagram video and uploads it for processing.

    **Allowed File Types:**
    - video/mp4 (.mp4)
    - video/quicktime (.mov)
    - video/x-m4v (.m4v)

    **File Size Limit:** 500MB

    **Storage:**
    - Videos are stored locally on the server (temp/videos/)
    - Videos are automatically deleted after extraction
    - Orphaned videos are cleaned up every hour (2 hour TTL)

    **Workflow:**
    1. Mobile app receives `needs_client_download` status from extraction
    2. Mobile app downloads video from Instagram using user's IP
    3. Mobile app uploads video using this endpoint
    4. Mobile app calls `POST /extraction/jobs/{job_id}/resume` to continue extraction

    **Authentication:**
    - Requires valid JWT access token (Bearer token)
    - User must own the extraction job
    """
    if not job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="job_id is required"
        )

    upload_service = UploadService(supabase)

    try:
        result = await upload_service.save_video_locally(file, job_id)
        return VideoUploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while uploading the video"
        )
