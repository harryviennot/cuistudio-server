"""
Credits and subscription endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
import logging

from app.core.database import get_supabase_admin_client
from app.core.security import get_current_user
from app.services.credit_service import CreditService
from app.services.subscription_service import SubscriptionService
from app.api.v1.schemas.credits import (
    CreditsResponse,
    CanExtractResponse,
    SubscriptionStatusResponse,
)

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
