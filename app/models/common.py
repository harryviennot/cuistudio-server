"""
Common models and enums used across the application
"""
from pydantic import BaseModel
from enum import Enum


class SourceType(str, Enum):
    """Types of recipe sources"""
    video = "video"
    image = "image"
    text = "text"


class JobStatus(str, Enum):
    """Status of processing jobs"""
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


