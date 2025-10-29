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

        # Check if user has completed profile by querying database (source of truth)
        is_new_user = True
        try:
            profile_result = supabase.from_("users").select("id, profile_completed").eq("id", user.id).execute()
            # User has profile if record exists in database
            is_new_user = len(profile_result.data) == 0
        except Exception as e:
            logger.warning(f"Failed to check profile completion status: {e}")
            # Fallback to metadata if database check fails
            is_new_user = not user.user_metadata.get("profile_completed", False)

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
