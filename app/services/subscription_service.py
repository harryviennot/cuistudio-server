"""
Subscription service for managing RevenueCat subscriptions.

This service syncs subscription data from RevenueCat webhooks
and provides methods to check subscription status.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from supabase import Client
import logging

from app.domain.enums import SubscriptionStatus

logger = logging.getLogger(__name__)

# RevenueCat entitlement identifier for premium access
# This must match the entitlement ID configured in RevenueCat dashboard
PRO_ENTITLEMENT_ID = "Cuisto Pro"


class SubscriptionService:
    """Service for managing user subscriptions"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's subscription record"""
        try:
            response = self.supabase.table("user_subscriptions").select("*").eq("user_id", user_id).execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error getting subscription for user {user_id}: {e}")
            raise

    async def is_premium(self, user_id: str) -> bool:
        """Check if user has an active premium subscription"""
        try:
            subscription = await self.get_subscription(user_id)

            if not subscription:
                return False

            if not subscription.get("is_active"):
                return False

            # Check if subscription has expired
            expires_at = subscription.get("expires_at")
            if expires_at:
                expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expires < datetime.now(timezone.utc):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking premium status for user {user_id}: {e}")
            return False

    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Get detailed subscription status for API response"""
        try:
            subscription = await self.get_subscription(user_id)

            if not subscription:
                return {
                    "status": SubscriptionStatus.NONE.value,
                    "is_premium": False,
                    "is_trialing": False,
                    "product_id": None,
                    "expires_at": None,
                    "will_renew": False
                }

            is_active = subscription.get("is_active", False)
            is_trial = subscription.get("is_trial", False)
            expires_at = subscription.get("expires_at")

            # Determine status
            if is_active:
                if is_trial:
                    status = SubscriptionStatus.TRIALING
                else:
                    status = SubscriptionStatus.ACTIVE
            else:
                # Check if expired
                if expires_at:
                    expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    if expires < datetime.now(timezone.utc):
                        status = SubscriptionStatus.EXPIRED
                    else:
                        status = SubscriptionStatus.CANCELLED
                else:
                    status = SubscriptionStatus.EXPIRED

            return {
                "status": status.value,
                "is_premium": is_active,
                "is_trialing": is_trial,
                "product_id": subscription.get("product_id"),
                "expires_at": expires_at,
                "will_renew": is_active and not is_trial
            }

        except Exception as e:
            logger.error(f"Error getting subscription status for user {user_id}: {e}")
            raise

    async def sync_from_revenuecat(
        self,
        user_id: str,
        customer_info: Dict[str, Any]
    ) -> None:
        """
        Sync subscription data from RevenueCat customer info.
        Handles both v1 (webhooks) and v2 (API) response formats.
        """
        try:
            logger.info(f"Syncing RevenueCat data for user {user_id}")
            logger.debug(f"Customer info: {customer_info}")

            # Detect response format and extract entitlements
            # v2 API format: { "active_entitlements": { "items": [...] }, "id": "..." }
            # v1 webhook format: { "id": "...", "subscriber": { "entitlements": {...} } }

            pro_entitlement = None
            revenuecat_customer_id = ""

            if "active_entitlements" in customer_info:
                # v2 API format
                revenuecat_customer_id = customer_info.get("id", "")
                entitlements_items = customer_info.get("active_entitlements", {}).get("items", [])

                # In v2 API, if there are any active entitlements, the user has premium
                # (We only have one entitlement "Cuisto Pro")
                if entitlements_items:
                    # Get the first active entitlement
                    ent = entitlements_items[0]
                    pro_entitlement = {
                        "entitlement_id": ent.get("entitlement_id"),
                        # expires_at in v2 is a Unix timestamp in milliseconds
                        "expires_at": ent.get("expires_at"),
                    }
                    logger.info(f"Found active entitlement for user {user_id}: {pro_entitlement}")

            elif "subscriber" in customer_info:
                # v1 webhook format
                revenuecat_customer_id = customer_info.get("id", "")
                entitlements = customer_info.get("subscriber", {}).get("entitlements", {})
                pro_entitlement = entitlements.get(PRO_ENTITLEMENT_ID, {})
                # Convert empty dict to None
                if not pro_entitlement:
                    pro_entitlement = None
            else:
                # Unknown format
                revenuecat_customer_id = customer_info.get("id", "")
                logger.warning(f"Unknown RevenueCat response format for user {user_id}")

            if pro_entitlement:
                # Handle both v1 and v2 field names
                # v1 uses ISO date strings, v2 uses Unix timestamps in ms
                expires_raw = pro_entitlement.get("expires_date") or pro_entitlement.get("expires_at")

                # Convert expires to ISO string if it's a Unix timestamp
                if isinstance(expires_raw, int):
                    # Unix timestamp in milliseconds
                    expires_date = datetime.fromtimestamp(expires_raw / 1000, tz=timezone.utc).isoformat()
                else:
                    expires_date = expires_raw

                product_id = pro_entitlement.get("product_identifier") or pro_entitlement.get("product_id")
                original_purchase = pro_entitlement.get("original_purchase_date") or pro_entitlement.get("original_purchase_at")
                period_type = pro_entitlement.get("period_type", "").lower()

                # Check if still active
                if expires_date:
                    expires_dt = datetime.fromisoformat(expires_date.replace("Z", "+00:00"))
                    is_active = expires_dt > datetime.now(timezone.utc)
                else:
                    is_active = True  # No expiry means lifetime access

                subscription_data = {
                    "user_id": user_id,
                    "revenuecat_customer_id": revenuecat_customer_id,
                    "product_id": product_id,
                    "entitlement_id": PRO_ENTITLEMENT_ID,
                    "is_active": is_active,
                    "expires_at": expires_date,
                    "original_purchase_date": original_purchase,
                    "is_trial": period_type == "trial",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                logger.info(f"User {user_id} subscription: active={is_active}, expires={expires_date}")
            else:
                # No active entitlement
                subscription_data = {
                    "user_id": user_id,
                    "revenuecat_customer_id": revenuecat_customer_id,
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                logger.info(f"User {user_id} has no active entitlements")

            # Upsert subscription
            self.supabase.table("user_subscriptions").upsert(
                subscription_data,
                on_conflict="user_id"
            ).execute()

            logger.info(f"Synced subscription for user {user_id}: active={subscription_data.get('is_active')}")

        except Exception as e:
            logger.error(f"Error syncing subscription for user {user_id}: {e}")
            raise

    async def handle_webhook_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Handle RevenueCat webhook events.
        """
        try:
            # Extract user ID from app_user_id
            app_user_id = event_data.get("app_user_id")
            if not app_user_id:
                logger.warning(f"Webhook event {event_type} missing app_user_id")
                return

            # RevenueCat sends the full customer info in the webhook
            customer_info = {
                "id": event_data.get("id"),
                "subscriber": {
                    "entitlements": event_data.get("subscriber", {}).get("entitlements", {})
                }
            }

            # Log the event type
            logger.info(f"Processing RevenueCat webhook: {event_type} for user {app_user_id}")

            # Sync subscription data
            await self.sync_from_revenuecat(app_user_id, customer_info)

            # Handle specific event types if needed
            if event_type == "INITIAL_PURCHASE":
                logger.info(f"New subscription for user {app_user_id}")
            elif event_type == "RENEWAL":
                logger.info(f"Subscription renewed for user {app_user_id}")
            elif event_type == "CANCELLATION":
                logger.info(f"Subscription cancelled for user {app_user_id}")
            elif event_type == "EXPIRATION":
                logger.info(f"Subscription expired for user {app_user_id}")
            elif event_type == "BILLING_ISSUE":
                logger.warning(f"Billing issue for user {app_user_id}")

        except Exception as e:
            logger.error(f"Error handling webhook event {event_type}: {e}")
            raise
