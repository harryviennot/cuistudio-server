"""
Security utilities and authentication
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
import logging

from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> dict:
    """
    Validate JWT token and return current user.

    Args:
        credentials: HTTP Bearer token
        supabase: Supabase client

    Returns:
        User dict with id, email, and other user data

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Verify token with Supabase
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = user_response.user

        # Check if user has completed onboarding by querying database (source of truth)
        is_new_user = True
        try:
            user_result = supabase.from_("users").select("id, onboarding_completed").eq("id", user.id).execute()
            if user_result.data:
                # User exists in database, check onboarding status
                is_new_user = not user_result.data[0].get("onboarding_completed", False)
            else:
                # User doesn't exist in users table yet, definitely new
                is_new_user = True
        except Exception as e:
            logger.warning(f"Failed to check onboarding completion status: {e}")
            # Default to new user if check fails
            is_new_user = True

        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "created_at": user.created_at,
            "user_metadata": user.user_metadata or {},
            "is_new_user": is_new_user,
            "is_anonymous": getattr(user, 'is_anonymous', False)
        }

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None


async def get_authenticated_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Require a fully authenticated (non-anonymous) user.
    Used for endpoints that require a real user account (email or phone linked).

    Raises:
        HTTPException: If user is anonymous
    """
    if current_user.get("is_anonymous", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a full account. Please link an email or phone number to continue.",
        )

    return current_user


def is_anonymous_user(user: dict) -> bool:
    """
    Check if a user is anonymous.

    Args:
        user: User dict from get_current_user

    Returns:
        True if user is anonymous, False otherwise
    """
    return user.get("is_anonymous", False)


async def get_admin_user(
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
) -> dict:
    """
    Require an admin user.
    Used for moderation/admin endpoints.

    Raises:
        HTTPException: If user is not an admin
    """
    try:
        # Check if user has admin flag in database
        user_result = supabase.from_("users")\
            .select("id, is_admin")\
            .eq("id", current_user["id"])\
            .single()\
            .execute()

        if not user_result.data or not user_result.data.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        current_user["is_admin"] = True
        return current_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
