"""
Push Notification Service

Handles sending push notifications via Expo Push API.
Documentation: https://docs.expo.dev/push-notifications/sending-notifications/
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import httpx
import logging
from enum import Enum

from app.core.config import get_settings
from app.repositories.push_token_repository import PushTokenRepository
from app.repositories.notification_preferences_repository import NotificationPreferencesRepository
from app.services.translation_service import get_translation_service, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class NotificationType(str, Enum):
    """Notification types for tracking and preferences"""
    FIRST_RECIPE_NUDGE = "first_recipe_nudge"
    WEEKLY_CREDITS_REFRESH = "weekly_credits_refresh"
    REFERRAL_ACTIVATED = "referral_activated"
    COOK_TONIGHT = "cook_tonight"
    COOKING_STREAK = "cooking_streak"
    MISS_YOU = "miss_you"


class PushNotificationService:
    """Service for sending push notifications via Expo Push API"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.settings = get_settings()
        self.token_repo = PushTokenRepository(supabase)
        self.preferences_repo = NotificationPreferencesRepository(supabase)
        self.translation_service = get_translation_service()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Expo Push API request"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Add access token if configured (recommended for production)
        if self.settings.EXPO_ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {self.settings.EXPO_ACCESS_TOKEN}"

        return headers

    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        check_preferences: bool = True
    ) -> bool:
        """
        Send a push notification to a user.

        Args:
            user_id: The target user's ID
            notification_type: Type of notification (for preferences and tracking)
            title: Notification title
            body: Notification body text
            data: Optional payload data for deep linking
            check_preferences: Whether to check user's notification preferences

        Returns:
            True if notification was sent successfully to at least one device
        """
        try:
            # Check if user has this notification type enabled
            if check_preferences:
                if not await self.preferences_repo.is_preference_enabled(
                    user_id, notification_type.value
                ):
                    logger.info(
                        f"Notification {notification_type.value} disabled for user {user_id}"
                    )
                    return False

            # Get active tokens for user
            tokens = await self.token_repo.get_active_tokens_for_user(user_id)

            if not tokens:
                logger.info(f"No active push tokens for user {user_id}")
                return False

            # Prepare messages
            messages = [
                {
                    "to": token,
                    "title": title,
                    "body": body,
                    "data": data or {},
                    "sound": "default",
                    "priority": "high",
                }
                for token in tokens
            ]

            # Send to Expo
            success = await self._send_to_expo(messages)

            # Log to notification history
            if success:
                await self._log_notification(
                    user_id=user_id,
                    notification_type=notification_type.value,
                    title=title,
                    body=body,
                    data=data
                )

            return success

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False

    async def send_bulk_notifications(
        self,
        user_ids: List[str],
        notification_type: NotificationType,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        check_preferences: bool = True
    ) -> Dict[str, bool]:
        """
        Send notifications to multiple users efficiently.

        Args:
            user_ids: List of target user IDs
            notification_type: Type of notification
            title: Notification title
            body: Notification body text
            data: Optional payload data
            check_preferences: Whether to check preferences

        Returns:
            Dict mapping user_id to success status
        """
        results: Dict[str, bool] = {}

        if not user_ids:
            return results

        try:
            # Filter by preferences if needed
            eligible_user_ids = user_ids
            if check_preferences:
                eligible_user_ids = await self.preferences_repo.get_users_with_preference_enabled(
                    user_ids, notification_type.value
                )

            if not eligible_user_ids:
                return {uid: False for uid in user_ids}

            # Get tokens for all eligible users
            tokens_by_user = await self.token_repo.get_all_active_tokens_for_users(
                eligible_user_ids
            )

            # Prepare all messages
            messages = []
            user_for_message: List[str] = []  # Track which user each message is for

            for user_id in eligible_user_ids:
                tokens = tokens_by_user.get(user_id, [])
                for token in tokens:
                    messages.append({
                        "to": token,
                        "title": title,
                        "body": body,
                        "data": data or {},
                        "sound": "default",
                        "priority": "high",
                    })
                    user_for_message.append(user_id)

            if not messages:
                return {uid: False for uid in user_ids}

            # Send in batches of 100 (Expo limit)
            batch_size = 100
            successful_users: set = set()

            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                batch_users = user_for_message[i:i + batch_size]

                if await self._send_to_expo(batch):
                    successful_users.update(batch_users)

            # Log notifications for successful sends
            for user_id in successful_users:
                await self._log_notification(
                    user_id=user_id,
                    notification_type=notification_type.value,
                    title=title,
                    body=body,
                    data=data
                )

            # Build results
            for uid in user_ids:
                results[uid] = uid in successful_users

            return results

        except Exception as e:
            logger.error(f"Error in bulk notification send: {e}")
            return {uid: False for uid in user_ids}

    async def _send_to_expo(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Send messages to Expo Push API.

        Handles response parsing and token invalidation.
        """
        if not messages:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    EXPO_PUSH_URL,
                    json=messages,
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(
                        f"Expo Push API error: {response.status_code} - {response.text}"
                    )
                    return False

                result = response.json()
                data = result.get("data", [])

                # Process results and handle invalid tokens
                success_count = 0
                for i, ticket in enumerate(data):
                    if ticket.get("status") == "ok":
                        success_count += 1
                    elif ticket.get("status") == "error":
                        error_type = ticket.get("details", {}).get("error")
                        token = messages[i]["to"]

                        # Handle invalid tokens
                        if error_type in ("DeviceNotRegistered", "InvalidCredentials"):
                            logger.info(f"Deactivating invalid token: {token[:30]}...")
                            await self.token_repo.deactivate_token(token)
                        else:
                            logger.warning(
                                f"Push notification error for token {token[:30]}...: "
                                f"{ticket.get('message')}"
                            )

                logger.info(f"Push notifications sent: {success_count}/{len(messages)} successful")
                return success_count > 0

        except httpx.TimeoutException:
            logger.error("Expo Push API request timed out")
            return False
        except Exception as e:
            logger.error(f"Error sending to Expo Push API: {e}")
            return False

    async def _log_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        expo_ticket_id: Optional[str] = None
    ) -> None:
        """Log notification to history table for analytics and deduplication"""
        try:
            self.supabase.table("notification_history").insert({
                "user_id": user_id,
                "notification_type": notification_type,
                "title": title,
                "body": body,
                "data": data or {},
                "expo_ticket_id": expo_ticket_id,
                "status": "sent"
            }).execute()
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
            # Don't raise - logging is not critical

    async def _get_user_language(self, user_id: str) -> str:
        """Get user's preferred language for notifications"""
        try:
            result = self.supabase.table("users")\
                .select("preferred_language")\
                .eq("id", user_id)\
                .execute()

            if result.data and result.data[0].get("preferred_language"):
                return result.data[0]["preferred_language"]
        except Exception as e:
            logger.warning(f"Error fetching user language for {user_id}: {e}")

        return DEFAULT_LANGUAGE

    # ===== Convenience methods for specific notification types =====

    async def send_first_recipe_nudge(self, user_id: str) -> bool:
        """Send first recipe nudge to user who hasn't extracted a recipe yet"""
        language = await self._get_user_language(user_id)
        title, body = self.translation_service.get_notification_text(
            "first_recipe_nudge", language
        )
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.FIRST_RECIPE_NUDGE,
            title=title,
            body=body,
            data={"screen": "new-recipe"}
        )

    async def send_weekly_credits_refresh(self, user_id: str, credits: int) -> bool:
        """Notify user their weekly credits have been refreshed"""
        language = await self._get_user_language(user_id)
        title, body = self.translation_service.get_notification_text(
            "weekly_credits_refresh", language, credits=credits
        )
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.WEEKLY_CREDITS_REFRESH,
            title=title,
            body=body,
            data={"screen": "new-recipe"}
        )

    async def send_referral_activated(
        self,
        user_id: str,
        referee_name: str,
        credits_earned: int
    ) -> bool:
        """Notify referrer when someone uses their code"""
        language = await self._get_user_language(user_id)
        title, body = self.translation_service.get_notification_text(
            "referral_activated", language,
            referee_name=referee_name, credits_earned=credits_earned
        )
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.REFERRAL_ACTIVATED,
            title=title,
            body=body,
            data={"screen": "settings", "section": "referral"}
        )

    async def send_cook_tonight(
        self,
        user_id: str,
        recipe_id: str,
        recipe_title: str
    ) -> bool:
        """Suggest a recipe to cook tonight"""
        language = await self._get_user_language(user_id)
        title, body = self.translation_service.get_notification_text(
            "cook_tonight", language, recipe_title=recipe_title
        )
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.COOK_TONIGHT,
            title=title,
            body=body,
            data={"screen": "recipe", "recipe_id": recipe_id}
        )

    async def send_cooking_streak(
        self,
        user_id: str,
        streak_days: int
    ) -> bool:
        """Celebrate cooking streak milestone"""
        language = await self._get_user_language(user_id)

        # Determine emoji and body key based on streak milestone
        if streak_days >= 30:
            emoji = " "
            body_key = "body_30"
        elif streak_days >= 14:
            emoji = " "
            body_key = "body_14"
        elif streak_days >= 7:
            emoji = " "
            body_key = "body_7"
        else:
            emoji = " "
            body_key = "body_default"

        title = self.translation_service.translate(
            "notifications.cooking_streak.title", language, emoji=emoji
        )
        body = self.translation_service.translate(
            f"notifications.cooking_streak.{body_key}", language, streak_days=streak_days
        )

        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.COOKING_STREAK,
            title=title,
            body=body,
            data={"screen": "library"}
        )

    async def send_miss_you(self, user_id: str) -> bool:
        """Re-engage user who hasn't been active"""
        language = await self._get_user_language(user_id)
        title, body = self.translation_service.get_notification_text(
            "miss_you", language
        )
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.MISS_YOU,
            title=title,
            body=body,
            data={"screen": "library"}
        )
