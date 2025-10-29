"""
Authentication schemas
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional


# ============================================================================
# PASSWORDLESS AUTHENTICATION REQUESTS
# ============================================================================

class EmailAuthRequest(BaseModel):
    """Email magic link authentication request (unified login/signup)"""
    email: EmailStr = Field(..., examples=["user@example.com"], description="Email address to send magic link")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com"
            }
        }
    }


class PhoneAuthRequest(BaseModel):
    """Phone OTP authentication request (unified login/signup)"""
    phone: str = Field(
        ...,
        pattern=r"^\+[1-9]\d{1,14}$",
        examples=["+15551234567"],
        description="Phone number in E.164 format"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "+15551234567"
            }
        }
    }


class VerifyEmailOTPRequest(BaseModel):
    """Verify email magic link token"""
    token_hash: str = Field(..., examples=["abc123def456"], description="Token hash from magic link URL")
    type: str = Field(default="email", examples=["email"], description="Verification type")

    model_config = {
        "json_schema_extra": {
            "example": {
                "token_hash": "abc123def456",
                "type": "email"
            }
        }
    }


class VerifyPhoneOTPRequest(BaseModel):
    """Phone OTP verification request"""
    phone: str = Field(..., pattern=r"^\+[1-9]\d{1,14}$", examples=["+15551234567"])
    token: str = Field(..., min_length=6, max_length=6, examples=["123456"], description="6-digit OTP code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "+15551234567",
                "token": "123456"
            }
        }
    }


# ============================================================================
# USER PROFILE COMPLETION
# ============================================================================

class CompleteProfileRequest(BaseModel):
    """Complete user profile for new users"""
    name: str = Field(..., min_length=1, max_length=100, examples=["John Doe"], description="Full name")
    date_of_birth: date = Field(..., examples=["1990-01-01"], description="Date of birth in YYYY-MM-DD format")
    bio: Optional[str] = Field(None, max_length=500, examples=["Food enthusiast and recipe collector"], description="User biography")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "date_of_birth": "1990-01-01",
                "bio": "Food enthusiast and recipe collector"
            }
        }
    }


class UpdateProfileRequest(BaseModel):
    """Update user profile"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, examples=["John Doe"])
    date_of_birth: Optional[date] = Field(None, examples=["1990-01-01"])
    bio: Optional[str] = Field(None, max_length=500, examples=["Food enthusiast and recipe collector"])

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "date_of_birth": "1990-01-01",
                "bio": "Food enthusiast and recipe collector"
            }
        }
    }


# ============================================================================
# AUTHENTICATION RESPONSES
# ============================================================================

class UserResponse(BaseModel):
    """User information response"""
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    user_metadata: Optional[dict] = None
    is_new_user: bool = False
    is_anonymous: bool = False


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    expires_in: int
    expires_at: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ============================================================================
# IDENTITY LINKING (ANONYMOUS TO AUTHENTICATED)
# ============================================================================

class LinkEmailIdentityRequest(BaseModel):
    """Link email identity to anonymous account"""
    email: EmailStr = Field(..., examples=["user@example.com"], description="Email address to link")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com"
            }
        }
    }


class LinkPhoneIdentityRequest(BaseModel):
    """Link phone identity to anonymous account"""
    phone: str = Field(
        ...,
        pattern=r"^\+[1-9]\d{1,14}$",
        examples=["+15551234567"],
        description="Phone number in E.164 format to link"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "+15551234567"
            }
        }
    }
