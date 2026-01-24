"""
Authentication endpoints - Passwordless Authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client, create_client
import logging

from app.core.database import get_supabase_client, get_supabase_admin_client
from app.core.config import get_settings
from app.core.security import get_current_user
from app.api.v1.schemas.auth import (
    EmailAuthRequest,
    PhoneAuthRequest,
    VerifyEmailOTPRequest,
    VerifyPhoneOTPRequest,
    CompleteProfileRequest,
    UpdateProfileRequest,
    SubmitOnboardingRequest,
    RefreshTokenRequest,
    LinkEmailIdentityRequest,
    LinkPhoneIdentityRequest,
    ChangeEmailRequest,
    VerifyEmailChangeRequest,
    UpdateLanguageRequest,
    AuthResponse,
    UserResponse,
    UserWarning
)
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ============================================================================
# ANONYMOUS AUTHENTICATION
# ============================================================================

@router.post(
    "/anonymous",
    response_model=AuthResponse,
    status_code=status.HTTP_410_GONE,
    summary="Anonymous Sign-in (Deprecated)",
    description="Anonymous authentication is no longer supported. Please use email or phone authentication.",
    responses={
        410: {
            "description": "Anonymous authentication is no longer supported",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Anonymous authentication is no longer supported. Please sign in with email or phone."
                    }
                }
            }
        }
    }
)
async def sign_in_anonymously():
    """
    ## Anonymous Sign-in (DEPRECATED)

    Anonymous authentication has been disabled. Users must authenticate with email or phone.

    **Alternative Authentication Methods:**
    - Use `/auth/email` to request an OTP code via email
    - Use `/auth/phone` to request an OTP code via SMS
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Anonymous authentication is no longer supported. Please sign in with email or phone."
    )


# ============================================================================
# IDENTITY LINKING (ANONYMOUS TO AUTHENTICATED)
# ============================================================================

@router.post(
    "/link-identity/email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Link Email to Anonymous Account",
    description="Convert anonymous user to authenticated by linking an email identity. Sends OTP code for verification.",
    responses={
        200: {
            "description": "OTP code sent for email verification",
            "content": {
                "application/json": {
                    "example": {"message": "Check your email! We've sent you a verification code to complete the upgrade."}
                }
            }
        },
        400: {"description": "User is already authenticated or email is invalid"},
        401: {"description": "Not authenticated"}
    }
)
async def link_email_identity(
    request: LinkEmailIdentityRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Link Email Identity to Anonymous Account

    Converts an anonymous user to an authenticated user by linking an email identity.

    **Requirements:**
    - User must be currently signed in as anonymous
    - User must not already have an email identity

    **Flow:**
    1. Anonymous user calls this endpoint with desired email
    2. System sends 6-digit OTP code to that email
    3. User enters OTP code in app
    4. Call `/auth/email/verify` to complete the linking
    5. Same UUID is kept, `is_anonymous` becomes `false`
    6. All recipes/cookbooks remain linked to the user

    **What Gets Preserved:**
    - User UUID stays the same
    - All created recipes
    - All cookbooks
    - All user preferences

    **What Changes:**
    - `is_anonymous` becomes `false`
    - Email is added to the account
    - User can now sign in with email OTP on other devices

    **Important:**
    - This is a one-way operation (cannot revert to anonymous)
    - User's data is now permanently tied to this email
    - Recommended to do this before user has significant data
    """
    try:
        # Check if user is anonymous
        if not current_user.get("is_anonymous", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an authenticated identity"
            )

        # Check if user already has an email
        if current_user.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an email identity"
            )

        settings = get_settings()

        # Update user with email identity via magic link
        # Supabase handles the identity linking automatically
        supabase.auth.update_user({
            "email": request.email
        })

        # Send OTP for email verification
        supabase.auth.sign_in_with_otp({
            "email": request.email,
            "options": {
                "should_create_user": False,  # Don't create new user, link to existing
                "email_redirect_to": f"{settings.SITE_URL}/auth/callback"
            }
        })

        return MessageResponse(
            message="Check your email! We've sent you a verification code to complete the upgrade."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email identity linking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link email identity: {str(e)}"
        )


@router.post(
    "/link-identity/phone",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Link Phone to Anonymous Account",
    description="Convert anonymous user to authenticated by linking a phone identity. Sends OTP for verification.",
    responses={
        200: {
            "description": "OTP sent for phone verification",
            "content": {
                "application/json": {
                    "example": {"message": "OTP sent to your phone. Please verify to complete the upgrade."}
                }
            }
        },
        400: {"description": "User is already authenticated or phone is invalid"},
        401: {"description": "Not authenticated"}
    }
)
async def link_phone_identity(
    request: LinkPhoneIdentityRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Link Phone Identity to Anonymous Account

    Converts an anonymous user to an authenticated user by linking a phone identity.

    **Requirements:**
    - User must be currently signed in as anonymous
    - User must not already have a phone identity

    **Flow:**
    1. Anonymous user calls this endpoint with desired phone number
    2. System sends 6-digit OTP to that phone
    3. User enters OTP in app
    4. Call `/auth/phone/verify` to complete the linking
    5. Same UUID is kept, `is_anonymous` becomes `false`
    6. All recipes/cookbooks remain linked to the user

    **What Gets Preserved:**
    - User UUID stays the same
    - All created recipes
    - All cookbooks
    - All user preferences

    **What Changes:**
    - `is_anonymous` becomes `false`
    - Phone number is added to the account
    - User can now sign in with phone OTP on other devices

    **Important:**
    - This is a one-way operation (cannot revert to anonymous)
    - User's data is now permanently tied to this phone number
    - Recommended to do this before user has significant data
    """
    try:
        # Check if user is anonymous
        if not current_user.get("is_anonymous", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an authenticated identity"
            )

        # Check if user already has a phone
        if current_user.get("phone"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has a phone identity"
            )

        # Update user with phone identity
        supabase.auth.update_user({
            "phone": request.phone
        })

        # Send OTP for phone verification
        supabase.auth.sign_in_with_otp({
            "phone": request.phone,
            "options": {
                "should_create_user": False  # Don't create new user, link to existing
            }
        })

        return MessageResponse(
            message="OTP sent to your phone. Please verify to complete the upgrade."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Phone identity linking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link phone identity: {str(e)}"
        )


# ============================================================================
# EMAIL OTP AUTHENTICATION (UNIFIED LOGIN/SIGNUP)
# ============================================================================

@router.post(
    "/email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Email OTP",
    description="Send a 6-digit OTP code to the user's email for passwordless authentication. Automatically creates user if they don't exist.",
    responses={
        200: {
            "description": "OTP code sent successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Check your email! We've sent you a verification code."}
                }
            }
        }
    }
)
async def send_email_otp(
    request: EmailAuthRequest,
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Email OTP Authentication (Unified Login/Signup)

    Sends a 6-digit one-time password to the provided email address.

    **Key Features:**
    - Unified endpoint for both login and signup
    - Automatically creates user if they don't exist
    - No password required
    - OTP expires in 3 minutes
    - Rate limited to prevent abuse

    **Flow:**
    1. User submits their email
    2. System sends 6-digit OTP code to email
    3. User enters OTP code in app
    4. Call `/auth/email/verify` with the OTP code to complete authentication

    **Security:**
    - Returns generic success message to prevent email enumeration
    - One-time use codes
    - Time-limited validity (3 minutes)
    """
    try:
        settings = get_settings()

        # sign_in_with_otp creates user if doesn't exist, sends OTP for both cases
        supabase.auth.sign_in_with_otp({
            "email": request.email,
            "options": {
                "should_create_user": True,
                "email_redirect_to": f"{settings.SITE_URL}/auth/callback"
            }
        })

        logger.info(f"OTP email sent successfully to {request.email}")

        return MessageResponse(
            message="Check your email! We've sent you a verification code."
        )

    except Exception as e:
        error_message = str(e)
        logger.error(f"Email OTP send error for {request.email}: {error_message}")
        logger.exception(e)  # Log full stack trace

        # Return generic message to prevent email enumeration
        return MessageResponse(
            message="Check your email! We've sent you a verification code."
        )


@router.post(
    "/email/verify",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Email OTP",
    description="Verify the 6-digit OTP code from email and complete authentication",
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
        400: {"description": "Invalid or expired OTP code"}
    }
)
async def verify_email_otp(
    request: VerifyEmailOTPRequest,
    supabase: Client = Depends(get_supabase_client),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    ## Verify Email OTP

    Validates the 6-digit OTP code and returns authentication tokens.

    **Request Body:**
    - `email`: The email address that received the OTP
    - `token`: The 6-digit OTP code from email
    - `type`: Must be "email"

    **Response:**
    - Returns JWT access token and refresh token
    - Includes user information with `is_new_user` flag
    - If `is_new_user` is true, frontend should redirect to onboarding

    **Next Steps:**
    - If `is_new_user === true`: Call `/auth/onboarding`
    - If `is_new_user === false`: User is fully authenticated, proceed to app
    """
    try:
        response = supabase.auth.verify_otp({
            "email": request.email,
            "token": request.token,
            "type": request.type
        })

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP code"
            )

        # Check if user is new by checking onboarding completion (source of truth)
        is_new_user = True
        try:
            user_result = admin_client.from_("users").select("onboarding_completed").eq("id", response.user.id).execute()
            if user_result.data:
                # User exists in database, check onboarding status
                is_new_user = not user_result.data[0].get("onboarding_completed", False)
            else:
                # User doesn't exist in users table yet, definitely new
                is_new_user = True
        except Exception as e:
            logger.warning(f"Failed to check onboarding status: {e}")
            # Default to new user if check fails
            is_new_user = True

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            phone=response.user.phone,
            created_at=response.user.created_at,
            user_metadata=response.user.user_metadata or {},
            is_new_user=is_new_user,
            is_anonymous=getattr(response.user, 'is_anonymous', False)
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
        logger.error(f"Email OTP verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification failed. The code may be invalid or expired."
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
        supabase.auth.sign_in_with_otp({
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
    supabase: Client = Depends(get_supabase_client),
    admin_client: Client = Depends(get_supabase_admin_client)
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
    - If `is_new_user === true`: Call `/auth/onboarding`
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

        # Check if user is new by checking onboarding completion (source of truth)
        is_new_user = True
        try:
            user_result = admin_client.from_("users").select("onboarding_completed").eq("id", response.user.id).execute()
            if user_result.data:
                # User exists in database, check onboarding status
                is_new_user = not user_result.data[0].get("onboarding_completed", False)
            else:
                # User doesn't exist in users table yet, definitely new
                is_new_user = True
        except Exception as e:
            logger.warning(f"Failed to check onboarding status: {e}")
            # Default to new user if check fails
            is_new_user = True

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            phone=response.user.phone,
            created_at=response.user.created_at,
            user_metadata=response.user.user_metadata or {},
            is_new_user=is_new_user,
            is_anonymous=getattr(response.user, 'is_anonymous', False)
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
        # DATABASE-FIRST PATTERN: Insert database record FIRST (fail-fast)
        # This ensures atomicity - if DB insert fails, nothing has changed
        user_record = {
            "id": current_user["id"],
            "name": profile.name,
            "date_of_birth": profile.date_of_birth.isoformat(),
            "bio": profile.bio,
            "email": current_user.get("email"),
            "phone": current_user.get("phone"),
            "profile_completed": True
        }

        # Step 1: Insert into database (CRITICAL - must succeed)
        db_result = admin_client.from_("users").upsert(user_record).execute()

        if not db_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save profile data"
            )

        # Step 2: Update metadata (OPTIONAL - for convenience/caching)
        # If this fails, it's non-critical since database is source of truth
        try:
            user_metadata = {
                "name": profile.name,
                "date_of_birth": profile.date_of_birth.isoformat(),
                "bio": profile.bio,
                "profile_completed": True
            }
            supabase.auth.update_user({"data": user_metadata})
        except Exception as metadata_error:
            # Log but don't fail - database record exists and is source of truth
            logger.warning(f"Failed to update user metadata (non-critical): {str(metadata_error)}")

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
        # DATABASE-FIRST PATTERN: Update database record FIRST (fail-fast)
        update_data = {}
        if profile.name is not None:
            update_data["name"] = profile.name
        if profile.date_of_birth is not None:
            update_data["date_of_birth"] = profile.date_of_birth.isoformat()
        if profile.bio is not None:
            update_data["bio"] = profile.bio

        if not update_data:
            return MessageResponse(message="No updates provided")

        # Add updated_at timestamp
        update_data["updated_at"] = "now()"

        # Step 1: Update database (CRITICAL - must succeed)
        db_result = admin_client.from_("users").update(update_data).eq("id", current_user["id"]).execute()

        if not db_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile data"
            )

        # Step 2: Sync metadata (OPTIONAL - for convenience/caching)
        # If this fails, it's non-critical since database is source of truth
        try:
            user_metadata = current_user.get("user_metadata", {})
            if profile.name is not None:
                user_metadata["name"] = profile.name
            if profile.date_of_birth is not None:
                user_metadata["date_of_birth"] = profile.date_of_birth.isoformat()
            if profile.bio is not None:
                user_metadata["bio"] = profile.bio

            supabase.auth.update_user({"data": user_metadata})
        except Exception as metadata_error:
            # Log but don't fail - database record is updated and is source of truth
            logger.warning(f"Failed to sync user metadata (non-critical): {str(metadata_error)}")

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
# ONBOARDING QUESTIONNAIRE
# ============================================================================

@router.post(
    "/onboarding",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Onboarding Questionnaire",
    description="Submit required onboarding questionnaire for new users. Tracks marketing and user preference data.",
    responses={
        200: {
            "description": "Onboarding completed successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Onboarding completed successfully!"}
                }
            }
        },
        400: {"description": "Validation error or onboarding already completed"},
        401: {"description": "Not authenticated"}
    }
)
async def submit_onboarding(
    request: SubmitOnboardingRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    ## Submit Onboarding Questionnaire

    Captures required onboarding data for new users including marketing attribution
    and user preferences. Must be completed before accessing the main app.

    **Required Fields:**
    - `heard_from`: How user discovered the app (social_media, friend, app_store, blog, search_engine, other)
    - `cooking_frequency`: How often user cooks (rarely, occasionally, regularly, almost_daily)
    - `recipe_sources`: Where user gets recipes (array: tiktok, instagram, youtube, blogs, cookbooks, family, other)

    **Optional Fields:**
    - `display_name`: User's preferred display name
    - `age`: User's age (13-120)

    **Data Usage:**
    - Marketing attribution tracking
    - User personalization
    - Feature usage analytics

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`

    **After Completion:**
    - User's `onboarding_completed` flag is set to `true`
    - User can now access the full application
    - `/auth/me` will return `is_new_user: false`
    """
    try:
        user_id = current_user["id"]

        # Check if onboarding already completed
        existing = admin_client.from_("user_onboarding").select("id").eq("user_id", user_id).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Onboarding already completed"
            )

        # Insert onboarding data
        onboarding_record = {
            "user_id": user_id,
            "heard_from": request.heard_from,
            "cooking_frequency": request.cooking_frequency,
            "recipe_sources": request.recipe_sources,
            "display_name": request.display_name,
            "age": request.age
        }

        onboarding_result = admin_client.from_("user_onboarding").insert(onboarding_record).execute()

        if not onboarding_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save onboarding data"
            )

        # Mark onboarding as completed in users table
        # Also update the user's name if display_name was provided
        user_update = {
            "onboarding_completed": True,
            "updated_at": "now()"
        }

        # Update name if display_name was provided during onboarding
        if request.display_name:
            user_update["name"] = request.display_name

        user_result = admin_client.from_("users").update(user_update).eq("id", user_id).execute()

        if not user_result.data:
            # If users table record doesn't exist, create it
            # Use display_name as name if provided, otherwise use email username
            default_name = request.display_name or current_user.get("email", "").split("@")[0] or "User"

            user_insert = {
                "id": user_id,
                "name": default_name,
                "onboarding_completed": True
            }
            user_result = admin_client.from_("users").insert(user_insert).execute()

            if not user_result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user onboarding status"
                )

        logger.info(f"Onboarding completed for user {user_id}")

        # Note: No longer creating default collections on signup.
        # Collections are now virtual (computed from user_recipe_data).

        return MessageResponse(message="Onboarding completed successfully!")

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        logger.error(f"Onboarding submission error: {error_message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {error_message}"
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
                        "is_new_user": False,
                        "unacknowledged_warnings": []
                    }
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def get_me(
    current_user: dict = Depends(get_current_user),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    ## Get Current User

    Retrieves information about the currently authenticated user.

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`

    **Response:**
    - Returns user information including metadata
    - Includes `is_new_user` flag indicating if profile completion is needed
    - Includes `unacknowledged_warnings` array with any pending warnings that require acknowledgment
    """
    # Fetch unacknowledged warnings for this user, including recipe details
    warnings = []
    try:
        # Join with recipes table to get title and image
        warnings_result = admin_client.from_("user_warnings")\
            .select("id, reason, recipe_id, created_at, recipes(title, image_url)")\
            .eq("user_id", current_user["id"])\
            .is_("acknowledged_at", "null")\
            .order("created_at", desc=True)\
            .execute()

        if warnings_result.data:
            warnings = [
                UserWarning(
                    id=w["id"],
                    reason=w["reason"],
                    recipe_id=w.get("recipe_id"),
                    recipe_title=w.get("recipes", {}).get("title") if w.get("recipes") else None,
                    recipe_image_url=w.get("recipes", {}).get("image_url") if w.get("recipes") else None,
                    created_at=w["created_at"]
                )
                for w in warnings_result.data
            ]
    except Exception as e:
        # Non-critical - log and continue without warnings
        logger.warning(f"Failed to fetch user warnings: {e}")

    # Check if user has ever registered a push token (for notification prompt logic)
    has_push_token = False
    try:
        token_result = admin_client.table("push_tokens")\
            .select("id")\
            .eq("user_id", current_user["id"])\
            .limit(1)\
            .execute()
        has_push_token = len(token_result.data) > 0
    except Exception as e:
        # Non-critical - log and continue
        logger.warning(f"Failed to check push token history: {e}")

    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email"),
        phone=current_user.get("phone"),
        created_at=current_user["created_at"],
        user_metadata=current_user.get("user_metadata", {}),
        is_new_user=current_user.get("is_new_user", False),
        is_anonymous=current_user.get("is_anonymous", False),
        unacknowledged_warnings=warnings,
        has_registered_push_token=has_push_token
    )


@router.post(
    "/warnings/{warning_id}/acknowledge",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Acknowledge Warning",
    description="Mark a warning as acknowledged by the user",
    responses={
        200: {
            "description": "Warning acknowledged successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Warning acknowledged"}
                }
            }
        },
        401: {"description": "Not authenticated"},
        404: {"description": "Warning not found or already acknowledged"}
    }
)
async def acknowledge_warning(
    warning_id: str,
    current_user: dict = Depends(get_current_user),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    ## Acknowledge Warning

    Marks a warning as acknowledged by setting the `acknowledged_at` timestamp.

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`

    **Security:**
    - Users can only acknowledge their own warnings
    - Already acknowledged warnings return 404
    """
    try:
        # Update the warning, ensuring it belongs to the current user
        result = admin_client.from_("user_warnings")\
            .update({"acknowledged_at": "now()"})\
            .eq("id", warning_id)\
            .eq("user_id", current_user["id"])\
            .is_("acknowledged_at", "null")\
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warning not found or already acknowledged"
            )

        logger.info(f"Warning {warning_id} acknowledged by user {current_user['id']}")
        return MessageResponse(message="Warning acknowledged")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging warning {warning_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge warning"
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
        401: {"description": "Invalid or expired refresh token"},
        403: {"description": "Anonymous users cannot refresh tokens"}
    }
)
async def refresh_token(
    request: RefreshTokenRequest,
    supabase: Client = Depends(get_supabase_client),
    admin_client: Client = Depends(get_supabase_admin_client)
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

    **Note:**
    - Anonymous users cannot refresh tokens. They must authenticate with email or phone.
    """
    try:
        response = supabase.auth.refresh_session(request.refresh_token)

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Block anonymous users from refreshing tokens
        if getattr(response.user, 'is_anonymous', False):
            logger.warning(f"Anonymous user {response.user.id} attempted to refresh token - blocked")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anonymous sessions are no longer supported. Please sign in with email or phone."
            )

        # Check if user is new by checking onboarding completion (source of truth)
        is_new_user = True
        try:
            user_result = admin_client.from_("users").select("onboarding_completed").eq("id", response.user.id).execute()
            if user_result.data:
                # User exists in database, check onboarding status
                is_new_user = not user_result.data[0].get("onboarding_completed", False)
            else:
                # User doesn't exist in users table yet, definitely new
                is_new_user = True
        except Exception as e:
            logger.warning(f"Failed to check onboarding status: {e}")
            # Default to new user if check fails
            is_new_user = True

        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            phone=response.user.phone,
            created_at=response.user.created_at,
            user_metadata=response.user.user_metadata or {},
            is_new_user=is_new_user,
            is_anonymous=getattr(response.user, 'is_anonymous', False)
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


# ============================================================================
# ACCOUNT MANAGEMENT
# ============================================================================

SYSTEM_ACCOUNT_ID = "00000000-0000-0000-0000-000000000000"


@router.post(
    "/email/change",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Email Change",
    description="Initiates email change process. Sends verification to new email address.",
    responses={
        200: {
            "description": "Verification email sent",
            "content": {
                "application/json": {
                    "example": {"message": "Verification email sent! Please check your new email address to confirm the change."}
                }
            }
        },
        400: {"description": "Email already in use"},
        401: {"description": "Not authenticated"}
    }
)
async def change_email(
    request: ChangeEmailRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user),
):
    """
    ## Change Account Email

    Initiates the email change process for passwordless authentication.

    **Flow:**
    1. User submits new email address
    2. Supabase sends verification email to the new address
    3. User clicks verification link in email
    4. Email is updated in auth.users

    **Note:**
    - Old email remains active until new email is verified
    - User should sign in with new email after verification

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`
    """
    try:
        user_id = current_user["id"]
        token = credentials.credentials

        # Create a user-authenticated Supabase client
        # This triggers the proper email verification flow (sends "Change Email Address" template)
        settings = get_settings()
        user_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
        user_client.auth.set_session(token, token)

        # Use update_user() which triggers email verification flow
        # Unlike admin.update_user_by_id(), this sends the verification email
        # The redirect URL is configured in Supabase Dashboard:
        # 1. Go to Auth > Email Templates > Change Email Address
        # 2. Use {{ .SiteURL }}/auth/email-confirmed as redirect in the template
        response = user_client.auth.update_user({"email": request.new_email})

        if response.user:
            logger.info(f"Email change initiated for user {user_id} to {request.new_email}")
            return MessageResponse(
                message="Verification email sent! Please check your new email address to confirm the change."
            )

        # If no user returned, something went wrong
        raise Exception("Failed to initiate email change - no user returned")

    except Exception as e:
        error_message = str(e)
        error_message_lower = error_message.lower()
        logger.error(f"Email change error for user {current_user['id']}: {error_message}")

        # Rate limit detection - Supabase returns "For security purposes, you can only request this after X seconds"
        if "security purposes" in error_message_lower and "seconds" in error_message_lower:
            # Extract the number of seconds from the message
            import re
            match = re.search(r'after (\d+) seconds', error_message)
            seconds = match.group(1) if match else "a few"
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {seconds} seconds before requesting another code."
            )

        # Comprehensive duplicate email detection patterns
        duplicate_indicators = [
            "already registered",
            "already exists",
            "duplicate",
            "unique constraint",
            "email_unique",
            "email address already",
            "user with this email",
            "email taken",
            "email is already",
            "a user with this email address has already been registered"
        ]

        if any(indicator in error_message_lower for indicator in duplicate_indicators):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered to another account."
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate email change. Please try again."
        )


@router.post(
    "/email/change/verify",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Email Change with OTP",
    description="Verifies email change using the 6-digit OTP code. Handles both single and double confirmation flows.",
    responses={
        200: {
            "description": "Email changed successfully or second OTP sent",
            "content": {
                "application/json": {
                    "examples": {
                        "complete": {"value": {"message": "Email changed successfully!"}},
                        "second_otp": {"value": {"message": "SECOND_OTP_SENT"}}
                    }
                }
            }
        },
        400: {"description": "Invalid or expired OTP code"},
        401: {"description": "Not authenticated"},
        500: {"description": "Server error"}
    }
)
async def verify_email_change(
    request: VerifyEmailChangeRequest,
    authorization: str = Header(..., description="Bearer token"),
    current_user: dict = Depends(get_current_user)
):
    """
    ## Verify Email Change with OTP

    Verifies the OTP code for email change. With "Secure email change" enabled
    in Supabase, this is a two-step process:

    **Flow (Secure email change enabled):**
    1. User initiates email change via `/email/change` endpoint
    2. Supabase sends OTP code to the CURRENT email address
    3. User enters the OTP code → this endpoint verifies it
    4. Supabase then sends a SECOND OTP to the NEW email address
    5. User enters that OTP → this endpoint verifies it and completes the change

    **Response:**
    - `{"message": "SECOND_OTP_SENT"}` - First OTP verified, second OTP sent to new email
    - `{"message": "Email changed successfully!"}` - Email change complete

    **Note:** The email is only changed after ALL required OTP verifications pass.
    If any verification fails, the original email remains unchanged.

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`
    """
    user_id = current_user["id"]
    current_email = current_user.get("email")

    if not current_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email associated with this account."
        )

    try:
        # Extract the token from the Authorization header
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

        # Create a user-authenticated client
        settings = get_settings()
        user_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
        user_client.auth.set_session(token, token)

        # Determine which email to use for verification
        # - First step: verify OTP sent to current email
        # - Second step: verify OTP sent to new email (request.email)
        # We try the new email first (second step), then fall back to current email (first step)

        # Try verifying with the new email first (second step of secure email change)
        try:
            response = user_client.auth.verify_otp({
                "email": request.email,
                "token": request.token,
                "type": "email_change"
            })

            if hasattr(response, 'user') and response.user:
                logger.info(f"Email successfully changed for user {user_id} to {request.email}")
                return MessageResponse(message="Email changed successfully!")
        except Exception as new_email_error:
            error_str = str(new_email_error)
            # Check if this is a "second OTP sent" response disguised as an error
            # Supabase returns {'code': '200', 'msg': 'Confirmation sent to the other email'}
            # which the Python client incorrectly tries to parse as a User object
            if "confirmation sent to the other email" in error_str.lower() or "sent to the other email" in error_str.lower():
                logger.info(f"First OTP verified for user {user_id}, second OTP sent to {request.email}")
                return MessageResponse(message="SECOND_OTP_SENT")
            logger.debug(f"New email verification failed, trying current email: {error_str}")

        # Try verifying with current email (first step of secure email change)
        try:
            response = user_client.auth.verify_otp({
                "email": current_email,
                "token": request.token,
                "type": "email_change"
            })

            # Check if this triggered a second OTP to the new email
            if hasattr(response, 'user') and response.user:
                logger.info(f"Email successfully changed for user {user_id} from {current_email} to {request.email}")
                return MessageResponse(message="Email changed successfully!")

            # If we get here with a 200-like response but no user, it means
            # the first OTP was verified and a second OTP was sent to the new email
            logger.info(f"First OTP verified for user {user_id}, second OTP sent to {request.email}")
            return MessageResponse(message="SECOND_OTP_SENT")

        except Exception as current_email_error:
            error_str = str(current_email_error)
            logger.debug(f"Current email verification exception: {error_str}")
            # Check if this is a "second OTP sent" response disguised as an error
            # The Supabase Python client throws a Pydantic validation error when it receives
            # {'code': '200', 'msg': 'Confirmation sent to the other email'} instead of a User object
            if "other email" in error_str.lower() or "'code': '200'" in error_str.lower():
                logger.info(f"First OTP verified for user {user_id}, second OTP sent to {request.email}")
                return MessageResponse(message="SECOND_OTP_SENT")
            # Re-raise for the outer exception handler
            raise

    except Exception as e:
        error_message = str(e)
        error_message_lower = error_message.lower()

        # Check if this is a "second OTP sent" response disguised as an error (fallback check)
        # The Supabase Python client throws a Pydantic validation error when it receives
        # {'code': '200', 'msg': 'Confirmation sent to the other email'} instead of a User object
        if "other email" in error_message_lower or "'code': '200'" in error_message:
            logger.info(f"First OTP verified for user {user_id}, second OTP sent to {request.email} (caught in outer handler)")
            return MessageResponse(message="SECOND_OTP_SENT")

        logger.error(f"Email change verification error for user {user_id}: {error_message}")

        # Check for invalid/expired OTP errors
        invalid_otp_indicators = [
            "invalid",
            "expired",
            "not found",
            "incorrect"
        ]

        if any(indicator in error_message_lower for indicator in invalid_otp_indicators):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code. Please request a new one."
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email change. Please try again."
        )


# ============================================================================
# USER PREFERENCES
# ============================================================================

@router.patch(
    "/me/language",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Preferred Language",
    description="Updates the user's preferred language for notifications.",
    responses={
        200: {
            "description": "Language updated successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Language preference updated to fr"}
                }
            }
        },
        400: {"description": "Invalid language code"},
        401: {"description": "Not authenticated"},
        500: {"description": "Server error"}
    }
)
async def update_language(
    request: UpdateLanguageRequest,
    current_user: dict = Depends(get_current_user),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    ## Update Preferred Language

    Updates the user's preferred language for push notifications and other
    server-side localized content.

    **Supported Languages:**
    - `en` - English (default)
    - `fr` - French

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`
    """
    try:
        user_id = current_user["id"]
        language = request.language

        # Update the user's preferred language
        result = admin_client.from_("users")\
            .update({"preferred_language": language, "updated_at": "now()"})\
            .eq("id", user_id)\
            .execute()

        if not result.data:
            # User record might not exist yet, try to create it
            insert_result = admin_client.from_("users")\
                .insert({
                    "id": user_id,
                    "preferred_language": language
                })\
                .execute()

            if not insert_result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update language preference"
                )

        logger.info(f"Updated language preference for user {user_id} to {language}")
        return MessageResponse(message=f"Language preference updated to {language}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Language update error for user {current_user['id']}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update language preference"
        )


@router.delete(
    "/account",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete Account",
    description="Permanently deletes the user account and associated data.",
    responses={
        200: {
            "description": "Account deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Account deleted successfully."}
                }
            }
        },
        401: {"description": "Not authenticated"},
        500: {"description": "Server error"}
    }
)
async def delete_account(
    current_user: dict = Depends(get_current_user),
    admin_client: Client = Depends(get_supabase_admin_client)
):
    """
    ## Delete Account

    Permanently deletes the user account with the following data handling:

    **Transferred to System Account:**
    - Recipes extracted from video URLs (TikTok, Instagram, YouTube)

    **Deleted:**
    - User's original recipes (non-video-extracted)
    - User profile data
    - User preferences and settings
    - Saved/bookmarked recipes
    - Cooking history

    **Anonymized:**
    - Fork attribution in recipe_contributors becomes "[Deleted User]"

    **Storage Cleanup:**
    - Recipe images owned by user
    - Cooking event photos

    **Warning:** This action is irreversible.

    **Authentication:**
    - Requires valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`
    """
    try:
        user_id = current_user["id"]

        logger.info(f"Starting account deletion for user {user_id}")

        # Step 1: Find video-extracted recipes owned by this user
        # These should be transferred to the system account, not deleted
        video_recipes_result = admin_client.from_("recipes")\
            .select("id")\
            .eq("created_by", user_id)\
            .eq("source_type", "video")\
            .execute()

        video_recipe_ids = []
        if video_recipes_result.data:
            video_recipe_ids = [r["id"] for r in video_recipes_result.data]

        # Step 2: Transfer video-extracted recipes to system account (if it exists)
        if video_recipe_ids:
            # Check if system account exists
            system_account = admin_client.from_("users")\
                .select("id")\
                .eq("id", SYSTEM_ACCOUNT_ID)\
                .execute()

            if system_account.data:
                # System account exists, transfer recipes
                admin_client.from_("recipes")\
                    .update({"created_by": SYSTEM_ACCOUNT_ID})\
                    .in_("id", video_recipe_ids)\
                    .execute()
                logger.info(f"Transferred {len(video_recipe_ids)} video-extracted recipes to system account")
            else:
                # System account doesn't exist - these recipes will be deleted by CASCADE
                # This is acceptable for now; video content attribution is preserved in video_sources table
                logger.warning(f"System account not found. {len(video_recipe_ids)} video-extracted recipes will be deleted with user.")

        # Step 3: Anonymize contributor records
        # Set display_name to "[Deleted User]" and user_id to NULL
        admin_client.from_("recipe_contributors")\
            .update({"display_name": "[Deleted User]", "user_id": None})\
            .eq("user_id", user_id)\
            .execute()

        logger.info(f"Anonymized contributor records for user {user_id}")

        # Step 4: Clean up storage (recipe-images and cooking-events buckets)
        for bucket_name in ["recipe-images", "cooking-events"]:
            try:
                # List files in user's folder
                files = admin_client.storage.from_(bucket_name).list(path=user_id)
                if files:
                    file_paths = [f"{user_id}/{f['name']}" for f in files]
                    admin_client.storage.from_(bucket_name).remove(file_paths)
                    logger.info(f"Deleted {len(file_paths)} files from {bucket_name}/{user_id}")
            except Exception as storage_error:
                # Non-critical - log and continue
                logger.warning(f"Storage cleanup error for {bucket_name}/{user_id} (non-critical): {storage_error}")

        # Step 5: Delete auth user (CASCADE handles public.users, remaining recipes, etc.)
        admin_client.auth.admin.delete_user(user_id)

        logger.info(f"Account deletion completed for user {user_id}")

        return MessageResponse(message="Account deleted successfully.")

    except Exception as e:
        import traceback
        logger.error(f"Account deletion error for user {current_user['id']}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error deleting user"
        )
