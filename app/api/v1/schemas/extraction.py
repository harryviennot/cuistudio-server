"""
Recipe extraction API schemas
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from app.domain.enums import SourceType, ExtractionStatus


class ExtractionSubmitRequest(BaseModel):
    """Submit content for recipe extraction"""
    source_type: SourceType
    source_url: Optional[str] = None
    text_content: Optional[str] = None  # For paste/voice transcription
    file_url: Optional[str] = None  # For uploaded photos


class ExtractionJobResponse(BaseModel):
    """Extraction job status response"""
    id: str
    user_id: str
    source_type: SourceType
    status: str
    recipe_id: Optional[str] = None
    error_message: Optional[str] = None
    progress_percentage: int
    current_step: Optional[str] = None
    created_at: str
    updated_at: str


class ExtractionStreamEvent(BaseModel):
    """WebSocket stream event"""
    event_type: str  # progress, completed, error
    job_id: str
    progress_percentage: Optional[int] = None
    current_step: Optional[str] = None
    recipe_id: Optional[str] = None
    error_message: Optional[str] = None
