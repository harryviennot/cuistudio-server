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
    """Email OTP authentication request (unified login/signup)"""
    email: EmailStr = Field(..., examples=["user@example.com"], description="Email address to send OTP code")

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
    """Verify email OTP code"""
    email: EmailStr = Field(..., examples=["user@example.com"], description="Email address that received the OTP")
    token: str = Field(..., min_length=6, max_length=6, examples=["123456"], description="6-digit OTP code from email")
    type: str = Field(default="email", examples=["email"], description="Verification type")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "token": "123456",
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
# ONBOARDING
# ============================================================================

class SubmitOnboardingRequest(BaseModel):
    """Submit onboarding questionnaire"""
    heard_from: str = Field(..., description="How user heard about app")
    cooking_frequency: str = Field(..., description="How often user cooks")
    recipe_sources: list[str] = Field(..., description="Where user gets recipes")
    display_name: Optional[str] = Field(None, description="Optional display name")
    age: Optional[int] = Field(None, ge=13, le=120, description="User's age")

    model_config = {
        "json_schema_extra": {
            "example": {
                "heard_from": "social_media",
                "cooking_frequency": "regularly",
                "recipe_sources": ["tiktok", "instagram", "youtube"],
                "display_name": "John",
                "age": 25
            }
        }
    }


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


# ============================================================================
# ACCOUNT MANAGEMENT
# ============================================================================

class ChangeEmailRequest(BaseModel):
    """Request to change account email"""
    new_email: EmailStr = Field(
        ...,
        examples=["newemail@example.com"],
        description="New email address to change to"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "new_email": "newemail@example.com"
            }
        }
    }
