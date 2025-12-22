"""
Credits and subscription endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
import httpx
import logging

from app.core.database import get_supabase_admin_client
from app.core.config import get_settings
from app.core.security import get_current_user
from app.services.credit_service import CreditService
from app.services.subscription_service import SubscriptionService
from app.api.v1.schemas.credits import (
    CreditsResponse,
    CanExtractResponse,
    SubscriptionStatusResponse,
)
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/credits", tags=["Credits"])


@router.get(
    "",
    response_model=CreditsResponse,
    summary="Get user credits",
    description="Get current user's credit balance and subscription status"
)
async def get_credits(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Get the current user's credit balance.

    Returns:
    - **standard_credits**: Weekly credits (5 first week, 3 after)
    - **referral_credits**: Bonus credits from referrals
    - **total_credits**: Total available credits
    - **is_first_week**: Whether user is in their first week
    - **next_reset_at**: When credits reset next (Monday 00:00 UTC)
    - **can_extract**: Whether user can perform an extraction
    - **is_premium**: Whether user has an active subscription
    """
    user_id = current_user["id"]

    subscription_service = SubscriptionService(supabase)
    credit_service = CreditService(supabase)

    is_premium = await subscription_service.is_premium(user_id)
    credits = await credit_service.get_credits_response(user_id, is_premium)

    return CreditsResponse(**credits)


@router.post(
    "/check",
    response_model=CanExtractResponse,
    summary="Check extraction eligibility",
    description="Pre-flight check to see if user can perform an extraction"
)
async def check_can_extract(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Check if the current user can perform an extraction.

    This is a pre-flight check that should be called before starting an extraction
    to provide a better user experience (show paywall before they wait for processing).

    Returns:
    - **can_extract**: True if user can extract
    - **reason**: Explanation (e.g., "premium", "3 credits available", "no_credits")
    - **credits_remaining**: Number of credits if applicable
    """
    user_id = current_user["id"]

    subscription_service = SubscriptionService(supabase)
    credit_service = CreditService(supabase)

    is_premium = await subscription_service.is_premium(user_id)
    can_extract, reason = await credit_service.can_extract(user_id, is_premium)

    credits_remaining = None
    if not is_premium and can_extract:
        credits = await credit_service.get_credits_response(user_id, is_premium)
        credits_remaining = credits["total_credits"]

    return CanExtractResponse(
        can_extract=can_extract,
        reason=reason,
        credits_remaining=credits_remaining
    )


@router.get(
    "/subscription",
    response_model=SubscriptionStatusResponse,
    summary="Get subscription status",
    description="Get current user's subscription status"
)
async def get_subscription_status(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Get the current user's subscription status.

    Returns:
    - **status**: none, active, trialing, expired, cancelled, or billing_issue
    - **is_premium**: Whether user has premium access
    - **is_trialing**: Whether user is in trial period
    - **product_id**: RevenueCat product identifier
    - **expires_at**: When subscription expires
    - **will_renew**: Whether subscription will auto-renew
    """
    user_id = current_user["id"]

    subscription_service = SubscriptionService(supabase)
    status_data = await subscription_service.get_subscription_status(user_id)

    return SubscriptionStatusResponse(**status_data)


@router.post(
    "/subscription/sync",
    response_model=SubscriptionStatusResponse,
    summary="Sync subscription from RevenueCat",
    description="Manually sync subscription status from RevenueCat. Use after a purchase."
)
async def sync_subscription(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Sync subscription status from RevenueCat.

    This endpoint fetches the latest customer info from RevenueCat
    and updates the local subscription record. Use this after a purchase
    to ensure the backend has the latest subscription status.

    This is a fallback for when webhooks are delayed or not configured.
    """
    user_id = current_user["id"]
    settings = get_settings()

    if not settings.REVENUECAT_API_KEY or not settings.REVENUECAT_PROJECT_ID:
        logger.error("RevenueCat not configured (missing API_KEY or PROJECT_ID)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RevenueCat not configured"
        )

    try:
        # Fetch customer info from RevenueCat API v2
        # https://www.revenuecat.com/docs/api-v2
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.revenuecat.com/v2/projects/{settings.REVENUECAT_PROJECT_ID}/customers/{user_id}",
                headers={
                    "Authorization": f"Bearer {settings.REVENUECAT_API_KEY}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 404:
                # User not found in RevenueCat - not an error, they just haven't purchased
                logger.info(f"User {user_id} not found in RevenueCat")
                return SubscriptionStatusResponse(
                    status="none",
                    is_premium=False,
                    is_trialing=False,
                    product_id=None,
                    expires_at=None,
                    will_renew=False
                )

            if response.status_code != 200:
                logger.error(f"RevenueCat API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to fetch subscription from RevenueCat"
                )

            customer_data = response.json()
            logger.info(f"RevenueCat API response for user {user_id}: {customer_data}")

        # Sync the subscription data to our database
        subscription_service = SubscriptionService(supabase)
        await subscription_service.sync_from_revenuecat(user_id, customer_data)

        # Return the updated status
        status_data = await subscription_service.get_subscription_status(user_id)
        return SubscriptionStatusResponse(**status_data)

    except httpx.RequestError as e:
        logger.error(f"RevenueCat request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to connect to RevenueCat"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription sync error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync subscription"
        )
