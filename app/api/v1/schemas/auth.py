"""
Authentication schemas
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class SignUpRequest(BaseModel):
    """User signup request"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordUpdateRequest(BaseModel):
    """Password update request"""
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """User information response"""
    id: str
    email: str
    created_at: datetime
    user_metadata: Optional[dict] = None


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int
    expires_at: Optional[int] = None
