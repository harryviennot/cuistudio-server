"""
User-related models
"""
from pydantic import BaseModel
from datetime import datetime


class UserResponse(BaseModel):
    """User information response model"""
    id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


