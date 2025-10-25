"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
import logging

from app.core.database import get_supabase_client
from app.core.security import get_current_user
from app.api.v1.schemas.auth import (
    SignUpRequest,
    LoginRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordUpdateRequest,
    AuthResponse,
    UserResponse
)
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    credentials: SignUpRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """Register a new user"""
    try:
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            created_at=response.user.created_at,
            user_metadata=response.user.user_metadata
        )

        # Check if session exists (it might be None if email confirmation is required)
        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_201_CREATED,
                detail="User created successfully. Please check your email to confirm your account."
            )

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            token_type="bearer",
            user=user_data,
            expires_in=response.session.expires_in or 3600,
            expires_at=response.session.expires_at
        )

    except Exception as e:
        error_message = str(e)

        if "User already registered" in error_message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        elif "Password should be at least" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        else:
            logger.error(f"Signup error: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {error_message}"
            )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: LoginRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """Authenticate user"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            created_at=response.user.created_at,
            user_metadata=response.user.user_metadata
        )

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            token_type="bearer",
            user=user_data,
            expires_in=response.session.expires_in or 3600,
            expires_at=response.session.expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)

        if "Invalid login credentials" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        else:
            logger.error(f"Login error: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {error_message}"
            )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Logout current user"""
    try:
        supabase.auth.sign_out()
        return MessageResponse(message="Successfully logged out")
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        created_at=current_user["created_at"],
        user_metadata=current_user.get("user_metadata")
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """Refresh access token"""
    try:
        response = supabase.auth.refresh_session(request.refresh_token)

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            created_at=response.user.created_at,
            user_metadata=response.user.user_metadata
        )

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            token_type="bearer",
            user=user_data,
            expires_in=response.session.expires_in or 3600,
            expires_at=response.session.expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/password-reset", response_model=MessageResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """Request password reset email"""
    try:
        supabase.auth.reset_password_email(request.email)

        # Always return success to prevent email enumeration
        return MessageResponse(
            message="If an account exists with this email, you will receive a password reset link"
        )

    except Exception as e:
        # Still return success to prevent email enumeration
        logger.error(f"Password reset error: {str(e)}")
        return MessageResponse(
            message="If an account exists with this email, you will receive a password reset link"
        )


@router.post("/password-update", response_model=MessageResponse)
async def update_password(
    request: PasswordUpdateRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update password for authenticated user"""
    try:
        supabase.auth.update_user({"password": request.password})

        return MessageResponse(message="Password updated successfully")

    except Exception as e:
        error_message = str(e)

        if "Password should be at least" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        else:
            logger.error(f"Password update error: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password update failed: {error_message}"
            )
