"""
Webhook endpoints for external services
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from supabase import Client
import logging
import hmac

from app.core.database import get_supabase_admin_client
from app.core.config import get_settings
from app.services.subscription_service import SubscriptionService
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def verify_revenuecat_signature(
    request: Request,
    x_revenuecat_signature: str = Header(None, alias="X-RevenueCat-Webhook-Secret")
) -> bool:
    """
    Verify RevenueCat webhook signature.
    RevenueCat uses a simple shared secret for webhook authentication.
    """
    settings = get_settings()

    if not settings.REVENUECAT_WEBHOOK_SECRET:
        logger.warning("REVENUECAT_WEBHOOK_SECRET not configured, skipping verification")
        return True

    if not x_revenuecat_signature:
        return False

    return hmac.compare_digest(
        x_revenuecat_signature,
        settings.REVENUECAT_WEBHOOK_SECRET
    )


@router.post(
    "/revenuecat",
    response_model=MessageResponse,
    summary="RevenueCat webhook",
    description="Handle RevenueCat subscription events"
)
async def revenuecat_webhook(
    request: Request,
    supabase: Client = Depends(get_supabase_admin_client),
    x_revenuecat_signature: str = Header(None, alias="X-RevenueCat-Webhook-Secret")
):
    """
    Handle RevenueCat webhook events.

    Supported events:
    - INITIAL_PURCHASE: New subscription
    - RENEWAL: Subscription renewed
    - CANCELLATION: Subscription cancelled
    - EXPIRATION: Subscription expired
    - BILLING_ISSUE: Payment failed
    - SUBSCRIBER_ALIAS: User alias created
    - PRODUCT_CHANGE: Subscription product changed
    - TRANSFER: Subscription transferred

    All events trigger a subscription sync from RevenueCat.
    """
    # Verify signature
    settings = get_settings()
    if settings.REVENUECAT_WEBHOOK_SECRET:
        if not x_revenuecat_signature or not hmac.compare_digest(
            x_revenuecat_signature,
            settings.REVENUECAT_WEBHOOK_SECRET
        ):
            logger.warning("Invalid RevenueCat webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )

    event_type = body.get("event", {}).get("type")
    event_data = body.get("event", {})

    if not event_type:
        logger.warning("Webhook missing event type")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event type"
        )

    logger.info(f"Received RevenueCat webhook: {event_type}")

    try:
        subscription_service = SubscriptionService(supabase)
        await subscription_service.handle_webhook_event(event_type, event_data)

        return MessageResponse(message=f"Processed {event_type}")

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Return 200 to prevent retries for transient errors
        # RevenueCat will retry on 5xx errors
        return MessageResponse(message=f"Error processing {event_type}, logged for review")
