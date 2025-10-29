"""
Image upload schemas
"""
from pydantic import BaseModel, Field
from typing import List


# ============================================================================
# CONSTANTS
# ============================================================================

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",      # JPEG alias
    "image/png",
    "image/heic",     # Apple HEIC
    "image/heif",     # HEIC variant
    "image/webp",
    "image/gif",      # GIF (static and animated)
}

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "heic", "heif", "webp", "gif"}

MAX_IMAGE_SIZE_MB = 50
MAX_IMAGES_PER_EXTRACTION = 5


# ============================================================================
# UPLOAD RESPONSES
# ============================================================================

class ImageUploadResponse(BaseModel):
    """Response for single image upload"""
    url: str = Field(..., description="Public URL of the uploaded image")
    path: str = Field(..., description="Storage path of the image")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the image")

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://project.supabase.co/storage/v1/object/public/recipe-images/user-id/uuid.jpg",
                "path": "user-id/uuid.jpg",
                "size": 1024000,
                "content_type": "image/jpeg"
            }
        }
    }


class MultipleImageUploadResponse(BaseModel):
    """Response for multiple image uploads"""
    images: List[ImageUploadResponse] = Field(..., description="List of uploaded images")
    total_count: int = Field(..., description="Total number of images uploaded")
    total_size: int = Field(..., description="Total size of all images in bytes")

    model_config = {
        "json_schema_extra": {
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
