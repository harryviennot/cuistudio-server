"""
Recipe extraction API schemas
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List
from app.domain.enums import SourceType, ExtractionStatus


class ExtractionSubmitRequest(BaseModel):
    """Submit content for recipe extraction"""
    source_type: SourceType
    source_url: Optional[str] = None
    source_urls: Optional[List[str]] = Field(None, max_length=5, description="List of source URLs (max 5)")
    text_content: Optional[str] = None  # For paste/voice transcription
    file_url: Optional[str] = None  # DEPRECATED: Use file_urls for single or multiple images
    file_urls: Optional[List[str]] = Field(None, max_length=5, description="List of uploaded file URLs (max 5)")

    @field_validator('source_urls', 'file_urls')
    @classmethod
    def validate_url_lists(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("URL list cannot be empty if provided")
        if v is not None and len(v) > 5:
            raise ValueError("Cannot provide more than 5 URLs")
        return v


class ExtractionJobResponse(BaseModel):
    """Extraction job status response"""
    id: str
    user_id: str
    source_type: SourceType
    source_urls: Optional[List[str]] = Field(None, description="List of source URLs for multi-image extraction")
    status: str
    recipe_id: Optional[str] = None
    error_message: Optional[str] = None
    progress_percentage: int
    current_step: Optional[str] = None
    created_at: str
    updated_at: str


class ImageExtractionResponse(BaseModel):
    """Response for image extraction submission"""
    job_id: str = Field(..., description="Extraction job ID for polling status")
    message: str = Field(default="Recipe extraction started. Poll /extraction/jobs/{job_id} for status.")
    image_count: int = Field(..., description="Number of images being processed")


class ExtractionStreamEvent(BaseModel):
    """WebSocket stream event"""
    event_type: str  # progress, completed, error
    job_id: str
    progress_percentage: Optional[int] = None
    current_step: Optional[str] = None
    recipe_id: Optional[str] = None
    error_message: Optional[str] = None
