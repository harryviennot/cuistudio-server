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
    SubmitOnboardingRequest,
    RefreshTokenRequest,
    LinkEmailIdentityRequest,
    LinkPhoneIdentityRequest,
    AuthResponse,
    UserResponse
)
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# ANONYMOUS AUTHENTICATION
# ============================================================================

@router.post(
    "/anonymous",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Anonymous Sign-in",
    description="Sign in anonymously without providing any credentials. Returns persistent user identity.",
    responses={
        200: {
            "description": "Anonymous sign-in successful",
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
                            "phone": None,
                            "created_at": "2024-01-01T00:00:00Z",
                            "user_metadata": {},
                            "is_new_user": True,
                            "is_anonymous": True
                        }
                    }
                }
            }
        }
    }
)
async def sign_in_anonymously(
    supabase: Client = Depends(get_supabase_client)
):
    """
    ## Anonymous Sign-in

    Creates a persistent anonymous user identity without requiring any credentials.

    **Key Features:**
    - No email, phone, or password required
    - User gets a permanent UUID that persists across sessions
    - JWT tokens work the same as authenticated users
    - User can be upgraded to authenticated later via identity linking
    - Anonymous users can create recipes and cookbooks

    **Use Cases:**
    - First-time app users who want to try features before signing up
    - Users who want to create recipes without creating an account
    - Temporary sessions that can be upgraded later

    **Token Storage:**
    - Frontend should store access_token and refresh_token securely
    - Tokens persist the anonymous user's session
    - When user reopens app, use stored tokens to maintain identity

    **Upgrading to Authenticated:**
    - Call `/auth/link-identity/email` or `/auth/link-identity/phone`
    - Same UUID is kept, just adds email/phone identity
    - All created recipes/cookbooks remain linked to the user

    **Session Persistence:**
    - As long as tokens are stored on device, user maintains same identity
    - If app is uninstalled, tokens are lost and user gets new identity on reinstall
    - Encourage users to link email/phone to prevent data loss

    **RLS Behavior:**
    - Anonymous users have `auth.uid()` just like authenticated users
    - They can create/read/update their own data
    - Subject to same Row Level Security policies
    """
    try:
        # Sign in anonymously via Supabase
        response = supabase.auth.sign_in_anonymously()

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create anonymous session"
            )

        # Anonymous users are always "new" on creation
        user_data = UserResponse(
            id=response.user.id,
            email=response.user.email,
            phone=response.user.phone,
            created_at=response.user.created_at,
            user_metadata=response.user.user_metadata or {},
            is_new_user=True,  # Anonymous users start as "new"
            is_anonymous=True  # Mark as anonymous
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
        logger.error(f"Anonymous sign-in error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anonymous sign-in failed: {str(e)}"
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

        from app.core.config import get_settings
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
        from app.core.config import get_settings
        settings = get_settings()

        # sign_in_with_otp creates user if doesn't exist, sends OTP for both cases
        response = supabase.auth.sign_in_with_otp({
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
        user_update = {
            "onboarding_completed": True,
            "updated_at": "now()"
        }

        user_result = admin_client.from_("users").update(user_update).eq("id", user_id).execute()

        if not user_result.data:
            # If users table record doesn't exist, create it
            # Use display_name as name if provided, otherwise use email username
            default_name = request.display_name or current_user.get("email", "").split("@")[0] or "User"

            user_insert = {
                "id": user_id,
                "email": current_user.get("email"),
                "phone": current_user.get("phone"),
                "name": default_name,  # Required field
                "onboarding_completed": True
            }
            user_result = admin_client.from_("users").insert(user_insert).execute()

            if not user_result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user onboarding status"
                )

        logger.info(f"Onboarding completed for user {user_id}")

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
    # is_new_user is already checked in get_current_user via database
    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email"),
        phone=current_user.get("phone"),
        created_at=current_user["created_at"],
        user_metadata=current_user.get("user_metadata", {}),
        is_new_user=current_user.get("is_new_user", False),
        is_anonymous=current_user.get("is_anonymous", False)
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
    """
    try:
        response = supabase.auth.refresh_session(request.refresh_token)

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
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
