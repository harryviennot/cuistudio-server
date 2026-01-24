"""
Push notification endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
import logging

from app.core.database import get_supabase_admin_client
from app.core.security import get_current_user
from app.repositories.push_token_repository import PushTokenRepository
from app.repositories.notification_preferences_repository import NotificationPreferencesRepository
from app.api.v1.schemas.notifications import (
    RegisterTokenRequest,
    RegisterTokenResponse,
    UnregisterTokenRequest,
    NotificationPreferencesResponse,
    UpdatePreferencesRequest,
    ActivityStatsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "/register-token",
    response_model=RegisterTokenResponse,
    summary="Register push token",
    description="Register a device push notification token"
)
async def register_push_token(
    request: RegisterTokenRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Register a push notification token for the current user's device.

    This should be called:
    - After the user grants notification permissions
    - On app startup if permissions are already granted

    The token will be associated with the current user and can receive
    push notifications via Expo Push API.

    Returns:
    - **success**: Whether registration succeeded
    - **message**: Status message
    """
    user_id = current_user["id"]

    try:
        token_repo = PushTokenRepository(supabase)
        await token_repo.register_token(
            user_id=user_id,
            expo_push_token=request.expo_push_token,
            platform=request.platform,
            device_id=request.device_id,
            app_version=request.app_version
        )

        logger.info(f"Registered push token for user {user_id}")
        return RegisterTokenResponse(
            success=True,
            message="Push token registered successfully"
        )
    except Exception as e:
        logger.error(f"Error registering push token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register push token"
        )


@router.post(
    "/unregister-token",
    response_model=RegisterTokenResponse,
    summary="Unregister push token",
    description="Unregister a device push notification token"
)
async def unregister_push_token(
    request: UnregisterTokenRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Unregister a push notification token.

    This should be called when:
    - User logs out
    - User disables notifications in device settings
    - App is uninstalled (if detectable)

    The token will be marked as inactive and won't receive further notifications.

    Returns:
    - **success**: Whether unregistration succeeded
    - **message**: Status message
    """
    try:
        token_repo = PushTokenRepository(supabase)
        await token_repo.deactivate_token(request.expo_push_token)

        logger.info(f"Unregistered push token for user {current_user['id']}")
        return RegisterTokenResponse(
            success=True,
            message="Push token unregistered successfully"
        )
    except Exception as e:
        logger.error(f"Error unregistering push token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister push token"
        )


@router.get(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Get notification preferences",
    description="Get current user's notification preferences"
)
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Get the current user's notification preferences.

    Creates default preferences if none exist.

    Returns all notification toggles and the user's timezone.
    """
    user_id = current_user["id"]

    try:
        prefs_repo = NotificationPreferencesRepository(supabase)
        prefs = await prefs_repo.get_or_create(user_id)

        return NotificationPreferencesResponse(
            notifications_enabled=prefs.get("notifications_enabled", True),
            first_recipe_nudge=prefs.get("first_recipe_nudge", True),
            weekly_credits_refresh=prefs.get("weekly_credits_refresh", True),
            referral_activated=prefs.get("referral_activated", True),
            cook_tonight=prefs.get("cook_tonight", True),
            cooking_streak=prefs.get("cooking_streak", True),
            miss_you=prefs.get("miss_you", True),
            timezone=prefs.get("timezone", "UTC")
        )
    except Exception as e:
        logger.error(f"Error fetching notification preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification preferences"
        )


@router.patch(
    "/preferences",
    response_model=NotificationPreferencesResponse,
    summary="Update notification preferences",
    description="Update notification preferences"
)
async def update_notification_preferences(
    request: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Update the current user's notification preferences.

    Only the fields provided in the request will be updated.
    Other fields will remain unchanged.

    Returns the updated preferences.
    """
    user_id = current_user["id"]

    try:
        prefs_repo = NotificationPreferencesRepository(supabase)

        # Build update dict from non-None values
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}

        if update_data:
            prefs = await prefs_repo.update_preferences(user_id, update_data)
        else:
            prefs = await prefs_repo.get_or_create(user_id)

        return NotificationPreferencesResponse(
            notifications_enabled=prefs.get("notifications_enabled", True),
            first_recipe_nudge=prefs.get("first_recipe_nudge", True),
            weekly_credits_refresh=prefs.get("weekly_credits_refresh", True),
            referral_activated=prefs.get("referral_activated", True),
            cook_tonight=prefs.get("cook_tonight", True),
            cooking_streak=prefs.get("cooking_streak", True),
            miss_you=prefs.get("miss_you", True),
            timezone=prefs.get("timezone", "UTC")
        )
    except Exception as e:
        logger.error(f"Error updating notification preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )


@router.get(
    "/activity-stats",
    response_model=ActivityStatsResponse,
    summary="Get activity stats",
    description="Get user's activity statistics including cooking streaks"
)
async def get_activity_stats(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Get the current user's activity statistics.

    Returns:
    - **current_cooking_streak**: Current consecutive cooking days
    - **longest_cooking_streak**: Longest ever cooking streak
    - **last_cook_date**: Date of last cooking session
    - **last_app_open_at**: Last time user was active in the app
    """
    user_id = current_user["id"]

    try:
        response = supabase.table("user_activity_stats")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()

        if response.data:
            stats = response.data[0]
            return ActivityStatsResponse(
                current_cooking_streak=stats.get("current_cooking_streak", 0),
                longest_cooking_streak=stats.get("longest_cooking_streak", 0),
                last_cook_date=stats.get("last_cook_date"),
                last_app_open_at=stats.get("last_app_open_at")
            )
        else:
            # No stats yet
            return ActivityStatsResponse(
                current_cooking_streak=0,
                longest_cooking_streak=0,
                last_cook_date=None,
                last_app_open_at=None
            )
    except Exception as e:
        logger.error(f"Error fetching activity stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch activity stats"
        )
