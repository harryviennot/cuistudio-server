"""
Authentication-related models
"""
from pydantic import BaseModel, Field
from typing import Optional

from app.models.user import UserResponse


class SignUpRequest(BaseModel):
    """User registration request"""
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class LoginRequest(BaseModel):
    """User login request"""
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response with tokens and user info"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    user: UserResponse
    expires_in: int
    expires_at: Optional[int] = None


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class PasswordUpdateRequest(BaseModel):
    """Password update request"""
    password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


