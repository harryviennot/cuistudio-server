"""
Recipe-related models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.common import SourceType, JobStatus


# Base models
class RecipeBase(BaseModel):
    """Base recipe model with common fields"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    source_type: SourceType
    ingredients: List[Dict[str, Any]] = Field(default_factory=list)
    instructions: List[Dict[str, Any]] = Field(default_factory=list)


class RatingBase(BaseModel):
    """Base rating model"""
    value: int = Field(..., ge=1, le=5)


# Create models
class RecipeCreate(RecipeBase):
    """Model for creating a new recipe"""
    user_id: str
    is_parsed: bool = False


class RecipeUpdate(BaseModel):
    """Model for updating an existing recipe"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    ingredients: Optional[List[Dict[str, Any]]] = None
    instructions: Optional[List[Dict[str, Any]]] = None


class RatingCreate(RatingBase):
    """Model for creating a rating"""
    pass


# Response models
class RecipeResponse(RecipeBase):
    """Recipe response with metadata"""
    id: str
    user_id: str
    rating_avg: float = 0.0
    is_parsed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RatingResponse(RatingBase):
    """Rating response with metadata"""
    id: str
    recipe_id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ParsingJobResponse(BaseModel):
    """Parsing job status response"""
    id: str
    recipe_id: str
    status: JobStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Submission model for recipe processing
class RecipeSubmission(BaseModel):
    """Model for submitting recipe content for processing"""
    title: Optional[str] = None
    description: Optional[str] = None
    source_type: SourceType
    source_url: Optional[str] = None
    text_content: Optional[str] = None  # For text-based recipes
    file_url: Optional[str] = None      # For uploaded files


