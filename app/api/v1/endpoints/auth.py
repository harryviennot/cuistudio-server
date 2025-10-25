"""
Authentication endpoints - Passwordless Authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
import logging

from app.core.database import get_supabase_client, get_supabase_admin_client
from app.core.security import get_current_user
from app.api.v1.schemas.auth import (
    EmailAuthRequest,
    PhoneAuthRequest,
    VerifyEmailOTPRequest,
    VerifyPhoneOTPRequest,
    CompleteProfileRequest,
    UpdateProfileRequest,
    RefreshTokenRequest,
    AuthResponse,
    UserResponse
)
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# EMAIL MAGIC LINK AUTHENTICATION (UNIFIED LOGIN/SIGNUP)
# ============================================================================

@router.post(
    "/email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Email Magic Link",
    description="Send a magic link to the user's email for passwordless authentication. Automatically creates user if they don't exist.",
    responses={
        200: {
            "description": "Magic link sent successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Check your email! We've sent you a magic link to sign in."}
                }
            }
        }
    }
)
async def authenticate_with_email(
    request: EmailAuthRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Email Magic Link Authentication (Unified Login/Signup)

    Sends a one-time use magic link to the provided email address.

    **Key Features:**
    - Unified endpoint for both login and signup
    - Automatically creates user if they don't exist
    - No password required
    - Magic link expires in 1 hour
    - Rate limited to prevent abuse

    **Flow:**
    1. User submits their email
    2. System sends magic link to email
    3. User clicks link in email
    4. User is redirected to your app with token
    5. Call `/auth/email/verify` to complete authentication

    **Security:**
    - Returns generic success message to prevent email enumeration
    - One-time use tokens
    - PKCE flow supported
    """
    try:
        from app.core.config import get_settings
        settings = get_settings()

        # sign_in_with_otp creates user if doesn't exist, sends magic link for both cases
        response = supabase.auth.sign_in_with_otp({
            "email": request.email,
            "options": {
                "should_create_user": True,
                "email_redirect_to": f"{settings.SITE_URL}/auth/callback"
            }
        })

        return MessageResponse(
            message="Check your email! We've sent you a magic link to sign in."
        )

    except Exception as e:
        error_message = str(e)
        logger.error(f"Email authentication error: {error_message}")

        # Return generic message to prevent email enumeration
        return MessageResponse(
            message="Check your email! We've sent you a magic link to sign in."
        )


@router.post(
    "/email/verify",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Email Magic Link",
    description="Verify the magic link token from email and complete authentication",
    responses={
        200: {
            "description": "Authentication successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh_token": "v1.MR45tLN-Io...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "user": {
                            "id": "uuid-here",
                            "email": "user@example.com",
                            "phone": None,
                            "created_at": "2024-01-01T00:00:00Z",
                            "user_metadata": {},
                            "is_new_user": True
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid or expired magic link"}
    }
)
async def verify_email_magic_link(
    request: VerifyEmailOTPRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Verify Email Magic Link

    Validates the magic link token and returns authentication tokens.

    **Request Body:**
    - `token_hash`: The token from the magic link URL
    - `type`: Must be "email"

    **Response:**
    - Returns JWT access token and refresh token
    - Includes user information with `is_new_user` flag
    - If `is_new_user` is true, frontend should redirect to profile completion

    **Next Steps:**
    - If `is_new_user === true`: Call `/auth/profile/complete`
    - If `is_new_user === false`: User is fully authenticated, proceed to app
    """
    try:
        response = supabase.auth.verify_otp({
            "token_hash": request.token_hash,
            "type": request.type
        })

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired magic link"
            )

        # Check if user is new (profile not completed)
        user_metadata = response.user.user_metadata or {}
        is_new_user = not user_metadata.get("profile_completed", False)

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            phone=response.user.phone,
            created_at=response.user.created_at,
            user_metadata=user_metadata,
            is_new_user=is_new_user
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
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Magic link verification failed. The link may be invalid or expired."
        )


# ============================================================================
# PHONE OTP AUTHENTICATION (UNIFIED LOGIN/SIGNUP)
# ============================================================================

@router.post(
    "/phone",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Phone OTP",
    description="Send a 6-digit OTP to the user's phone for passwordless authentication. Automatically creates user if they don't exist.",
    responses={
        200: {
            "description": "OTP sent successfully",
            "content": {
                "application/json": {
                    "example": {"message": "OTP sent to your phone number. Please verify to continue."}
                }
            }
        }
    }
)
async def authenticate_with_phone(
    request: PhoneAuthRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Phone OTP Authentication (Unified Login/Signup)

    Sends a 6-digit one-time password to the provided phone number via SMS.

    **Key Features:**
    - Unified endpoint for both login and signup
    - Automatically creates user if they don't exist
    - No password required
    - OTP expires in 60 seconds
    - Rate limited (5 SMS per hour)

    **Phone Format:**
    - Must be in E.164 format: `+[country_code][number]`
    - Example: `+15551234567`

    **Flow:**
    1. User submits their phone number
    2. System sends 6-digit OTP via SMS
    3. User enters OTP in app
    4. Call `/auth/phone/verify` with phone and OTP

    **Requirements:**
    - Twilio or compatible SMS provider configured
    - Phone provider enabled in Supabase
    """
    try:
        # sign_in_with_otp creates user if doesn't exist, sends OTP for both cases
        response = supabase.auth.sign_in_with_otp({
            "phone": request.phone,
            "options": {
                "should_create_user": True
            }
        })

        return MessageResponse(
            message="OTP sent to your phone number. Please verify to continue."
        )

    except Exception as e:
        error_message = str(e)
        logger.error(f"Phone authentication error: {error_message}")

        # Return generic message to prevent phone enumeration
        return MessageResponse(
            message="OTP sent to your phone number. Please verify to continue."
        )


@router.post(
    "/phone/verify",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Phone OTP",
    description="Verify the 6-digit OTP code sent to the user's phone",
    responses={
        200: {
            "description": "Authentication successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh_token": "v1.MR45tLN-Io...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "user": {
                            "id": "uuid-here",
                            "email": None,
                            "phone": "+15551234567",
                            "created_at": "2024-01-01T00:00:00Z",
                            "user_metadata": {},
                            "is_new_user": True
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid or expired OTP code"}
    }
)
async def verify_phone_otp(
    request: VerifyPhoneOTPRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Verify Phone OTP

    Validates the 6-digit OTP code and returns authentication tokens.

    **Request Body:**
    - `phone`: The phone number (E.164 format)
    - `token`: The 6-digit OTP code

    **Response:**
    - Returns JWT access token and refresh token
    - Includes user information with `is_new_user` flag

    **Next Steps:**
    - If `is_new_user === true`: Call `/auth/profile/complete`
    - If `is_new_user === false`: User is fully authenticated, proceed to app
    """
    try:
        response = supabase.auth.verify_otp({
            "phone": request.phone,
            "token": request.token,
            "type": "sms"
        })

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code"
            )

        # Check if user is new (profile not completed)
        user_metadata = response.user.user_metadata or {}
        is_new_user = not user_metadata.get("profile_completed", False)

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            phone=response.user.phone,
            created_at=response.user.created_at,
            user_metadata=user_metadata,
            is_new_user=is_new_user
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
        logger.error(f"Phone OTP verification error: {error_message}")

        if "Invalid" in error_message or "expired" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP code"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OTP verification failed: {error_message}"
            )


# ============================================================================
# USER PROFILE COMPLETION
# ============================================================================

@router.post(
    "/profile/complete",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete User Profile",
    description="Complete profile information for new users. Required after first authentication.",
    responses={
        200: {
            "description": "Profile completed successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Profile completed successfully!"}
                }
            }
        },
        400: {"description": "Username already taken or validation error"},
        401: {"description": "Not authenticated"}
    }
)
async def complete_profile(
    profile: CompleteProfileRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    ## Complete User Profile

    Completes the user profile for new users. This endpoint must be called when
    `is_new_user` is `true` in the authentication response.

    **Required Fields:**
    - `name`: Full name (1-100 characters)
    - `username`: Unique username (3-30 characters, alphanumeric + underscore)
    - `date_of_birth`: ISO date string (YYYY-MM-DD)

    **Optional Fields:**
    - `bio`: User biography (max 500 characters)

    **Validation:**
    - Username must be unique across all users
    - Username can only contain letters, numbers, and underscores
    - Date of birth must be valid date

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`

    **After Completion:**
    - User's `is_new_user` flag is set to `false`
    - User can now access the full application
    """
    try:
        # Update user metadata to mark profile as completed
        user_metadata = {
            "name": profile.name,
            "date_of_birth": profile.date_of_birth.isoformat(),
            "bio": profile.bio,
            "profile_completed": True
        }

        # Update auth user metadata
        supabase.auth.update_user({"data": user_metadata})

        # Insert or update profile in users table (using admin client to bypass RLS)
        try:
            user_record = {
                "id": current_user["id"],
                "name": profile.name,
                "date_of_birth": profile.date_of_birth.isoformat(),
                "bio": profile.bio,
                "email": current_user.get("email"),
                "phone": current_user.get("phone"),
                "profile_completed": True
            }
            admin_client.from_("users").upsert(user_record).execute()
        except Exception as db_error:
            logger.error(f"Failed to insert profile into users table: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save profile data"
            )

        return MessageResponse(message="Profile completed successfully!")

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        logger.error(f"Profile completion error: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete profile: {error_message}"
        )


@router.patch(
    "/profile",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
    description="Update profile information for existing users",
    responses={
        200: {
            "description": "Profile updated successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Profile updated successfully!"}
                }
            }
        },
        400: {"description": "Username already taken or validation error"},
        401: {"description": "Not authenticated"}
    }
)
async def update_profile(
    profile: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    ## Update User Profile

    Updates profile information for existing authenticated users.

    **Optional Fields:**
    - `name`: Full name (1-100 characters)
    - `username`: Unique username (3-30 characters, alphanumeric + underscore)
    - `date_of_birth`: ISO date string (YYYY-MM-DD)
    - `bio`: User biography (max 500 characters)

    **Validation:**
    - Only provided fields will be updated
    - Username must be unique if changed
    - Username can only contain letters, numbers, and underscores

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`
    """
    try:
        # Get current user metadata
        user_metadata = current_user.get("user_metadata", {})

        # Update only provided fields in metadata
        if profile.name is not None:
            user_metadata["name"] = profile.name
        if profile.date_of_birth is not None:
            user_metadata["date_of_birth"] = profile.date_of_birth.isoformat()
        if profile.bio is not None:
            user_metadata["bio"] = profile.bio

        # Update auth user metadata
        supabase.auth.update_user({"data": user_metadata})

        # Also update users table (using admin client to bypass RLS)
        try:
            update_data = {}
            if profile.name is not None:
                update_data["name"] = profile.name
            if profile.date_of_birth is not None:
                update_data["date_of_birth"] = profile.date_of_birth.isoformat()
            if profile.bio is not None:
                update_data["bio"] = profile.bio

            if update_data:
                admin_client.from_("users").update(update_data).eq("id", current_user["id"]).execute()
        except Exception as db_error:
            logger.error(f"Failed to update users table: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile data"
            )

        return MessageResponse(message="Profile updated successfully!")

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        logger.error(f"Profile update error: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {error_message}"
        )


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout User",
    description="Logout the currently authenticated user",
    responses={
        200: {
            "description": "Logout successful",
            "content": {
                "application/json": {
                    "example": {"message": "Successfully logged out"}
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def logout(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Logout User

    Logs out the currently authenticated user and invalidates their session.

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`

    **After Logout:**
    - Client should clear stored tokens
    - User must re-authenticate to access protected endpoints
    """
    try:
        supabase.auth.sign_out()
        return MessageResponse(message="Successfully logged out")
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Retrieve information about the currently authenticated user",
    responses={
        200: {
            "description": "User information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "uuid-here",
                        "email": "user@example.com",
                        "phone": None,
                        "created_at": "2024-01-01T00:00:00Z",
                        "user_metadata": {
                            "name": "John Doe",
                            "username": "johndoe",
                            "profile_completed": True
                        },
                        "is_new_user": False
                    }
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    ## Get Current User

    Retrieves information about the currently authenticated user.

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`

    **Response:**
    - Returns user information including metadata
    - Includes `is_new_user` flag indicating if profile completion is needed
    """
    user_metadata = current_user.get("user_metadata", {})
    is_new_user = not user_metadata.get("profile_completed", False)

    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email"),
        phone=current_user.get("phone"),
        created_at=current_user["created_at"],
        user_metadata=user_metadata,
        is_new_user=is_new_user
    )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Refresh an expired access token using a refresh token",
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh_token": "v1.MR45tLN-Io...",
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "user": {
                            "id": "uuid-here",
                            "email": "user@example.com",
                            "phone": None,
                            "created_at": "2024-01-01T00:00:00Z",
                            "user_metadata": {},
                            "is_new_user": False
                        }
                    }
                }
            }
        },
        401: {"description": "Invalid or expired refresh token"}
    }
)
async def refresh_token(
    request: RefreshTokenRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Refresh Access Token

    Refreshes an expired access token using a valid refresh token.

    **Use Case:**
    - Access tokens expire after 1 hour by default
    - Use this endpoint to get a new access token without re-authenticating
    - Refresh tokens are long-lived (typically 30+ days)

    **Request Body:**
    - `refresh_token`: The refresh token received during authentication

    **Response:**
    - Returns new access token and refresh token
    - Includes updated user information with `is_new_user` flag

    **Best Practices:**
    - Store refresh token securely (encrypted storage)
    - Implement automatic token refresh on 401 errors
    - Never expose refresh tokens in URLs or logs
    """
    try:
        response = supabase.auth.refresh_session(request.refresh_token)

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Check if user is new (profile not completed)
        user_metadata = response.user.user_metadata or {}
        is_new_user = not user_metadata.get("profile_completed", False)

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            phone=response.user.phone,
            created_at=response.user.created_at,
            user_metadata=user_metadata,
            is_new_user=is_new_user
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
