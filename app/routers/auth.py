from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from typing import Dict

from app.database import get_supabase_client
from app.models.auth import (
    SignUpRequest,
    LoginRequest,
    AuthResponse,
    PasswordResetRequest,
    PasswordUpdateRequest,
    RefreshTokenRequest,
)
from app.models.user import UserResponse
from app.models.common import MessageResponse
from app.auth import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    credentials: SignUpRequest,
    supabase: Client = Depends(get_supabase_client)
) -> AuthResponse:
    """
    Register a new user with email and password.
    """
    try:
        # Sign up the user with Supabase Auth
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        # Create user response
        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            created_at=response.user.created_at
        )
        
        # Return authentication response
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
        
        # Handle specific Supabase errors
        if "User already registered" in error_message or "already been registered" in error_message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        elif "Password should be at least" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        elif "Invalid email" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {error_message}"
            )

@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: LoginRequest,
    supabase: Client = Depends(get_supabase_client)
) -> AuthResponse:
    """
    Authenticate user with email and password.
    """
    try:
        # Sign in with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create user response
        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            created_at=response.user.created_at
        )
        
        # Return authentication response
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
        
        # Handle specific authentication errors
        if "Invalid login credentials" in error_message or "Invalid email or password" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        elif "Email not confirmed" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please confirm your email before logging in"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {error_message}"
            )

@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
) -> MessageResponse:
    """
    Logout the current user (invalidate session).
    """
    try:
        supabase.auth.sign_out()
        return MessageResponse(message="Successfully logged out")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user information.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    supabase: Client = Depends(get_supabase_client)
) -> AuthResponse:
    """
    Refresh access token using refresh token.
    """
    try:
        # Refresh the session
        response = supabase.auth.refresh_session(request.refresh_token)
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create user response
        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            created_at=response.user.created_at
        )
        
        # Return new authentication response
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.post("/password-reset", response_model=MessageResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    supabase: Client = Depends(get_supabase_client)
) -> MessageResponse:
    """
    Send password reset email to user.
    """
    try:
        # Request password reset
        supabase.auth.reset_password_email(request.email)
        
        # Always return success to prevent email enumeration
        return MessageResponse(
            message="If an account exists with this email, you will receive a password reset link"
        )
        
    except Exception as e:
        # Still return success to prevent email enumeration
        return MessageResponse(
            message="If an account exists with this email, you will receive a password reset link"
        )

@router.post("/password-update", response_model=MessageResponse)
async def update_password(
    request: PasswordUpdateRequest,
    current_user: Dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
) -> MessageResponse:
    """
    Update password for authenticated user.
    """
    try:
        # Update password
        supabase.auth.update_user({
            "password": request.password
        })
        
        return MessageResponse(message="Password updated successfully")
        
    except Exception as e:
        error_message = str(e)
        
        if "Password should be at least" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password update failed: {error_message}"
            )

@router.post("/verify-token", response_model=UserResponse)
async def verify_token(
    current_user: Dict = Depends(get_current_user)
) -> UserResponse:
    """
    Verify if the provided token is valid and return user info.
    Useful for checking authentication status on app startup.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )

