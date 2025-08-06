from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SourceType(str, Enum):
    video = "video"
    image = "image"
    text = "text"

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"

# Base models
class RecipeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    source_type: SourceType
    ingredients: List[Dict[str, Any]] = Field(default_factory=list)
    instructions: List[Dict[str, Any]] = Field(default_factory=list)

class RatingBase(BaseModel):
    value: int = Field(..., ge=1, le=5)

# Create models
class RecipeCreate(RecipeBase):
    user_id: str
    is_parsed: bool = False

class RecipeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    ingredients: Optional[List[Dict[str, Any]]] = None
    instructions: Optional[List[Dict[str, Any]]] = None

class RatingCreate(RatingBase):
    pass

# Response models
class RecipeResponse(RecipeBase):
    id: str
    user_id: str
    rating_avg: float = 0.0
    is_parsed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RatingResponse(RatingBase):
    id: str
    recipe_id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ParsingJobResponse(BaseModel):
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
    title: Optional[str] = None
    description: Optional[str] = None
    source_type: SourceType
    source_url: Optional[str] = None
    text_content: Optional[str] = None  # For text-based recipes
    file_url: Optional[str] = None      # For uploaded files

# User model
class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True 