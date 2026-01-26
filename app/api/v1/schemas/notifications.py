"""
Push notification API schemas
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class RegisterTokenRequest(BaseModel):
    """Request to register a push notification token"""
    expo_push_token: str = Field(
        ...,
        min_length=20,
        max_length=200,
        description="Expo push token (ExponentPushToken[...])"
    )
    platform: str = Field(
        ...,
        pattern="^(ios|android)$",
        description="Device platform: 'ios' or 'android'"
    )
    device_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional device identifier"
    )
    app_version: Optional[str] = Field(
        None,
        max_length=20,
        description="App version for compatibility tracking"
    )
    language: Optional[str] = Field(
        None,
        pattern="^(en|fr)$",
        description="User's preferred language for notifications"
    )


class RegisterTokenResponse(BaseModel):
    """Response for token registration"""
    success: bool
    message: str


class UnregisterTokenRequest(BaseModel):
    """Request to unregister a push notification token"""
    expo_push_token: str = Field(
        ...,
        min_length=20,
        max_length=200,
        description="Expo push token to unregister"
    )


class NotificationPreferencesResponse(BaseModel):
    """Response for notification preferences"""
    notifications_enabled: bool = Field(..., description="Master toggle")
    first_recipe_nudge: bool = Field(..., description="24h after signup nudge")
    weekly_credits_refresh: bool = Field(..., description="Monday credits reset notification")
    referral_activated: bool = Field(..., description="When someone uses your referral code")
    cook_tonight: bool = Field(..., description="Evening recipe suggestions")
    cooking_streak: bool = Field(..., description="Streak milestone celebrations")
    miss_you: bool = Field(..., description="Re-engagement after inactivity")
    timezone: str = Field(..., description="User timezone")


class UpdatePreferencesRequest(BaseModel):
    """Request to update notification preferences"""
    notifications_enabled: Optional[bool] = Field(None, description="Master toggle")
    first_recipe_nudge: Optional[bool] = Field(None, description="24h after signup nudge")
    weekly_credits_refresh: Optional[bool] = Field(None, description="Monday credits reset notification")
    referral_activated: Optional[bool] = Field(None, description="When someone uses your referral code")
    cook_tonight: Optional[bool] = Field(None, description="Evening recipe suggestions")
    cooking_streak: Optional[bool] = Field(None, description="Streak milestone celebrations")
    miss_you: Optional[bool] = Field(None, description="Re-engagement after inactivity")
    timezone: Optional[str] = Field(None, max_length=50, description="User timezone (e.g., 'America/New_York')")


class ActivityStatsResponse(BaseModel):
    """Response for user activity stats"""
    current_cooking_streak: int = Field(0, description="Current consecutive cooking days")
    longest_cooking_streak: int = Field(0, description="Longest ever cooking streak")
    last_cook_date: Optional[datetime] = Field(None, description="Last cooking session date")
    last_app_open_at: Optional[datetime] = Field(None, description="Last time user was active in the app")
