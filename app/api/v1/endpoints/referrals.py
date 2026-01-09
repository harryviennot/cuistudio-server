"""
Referral endpoints
"""
from fastapi import APIRouter, Depends
from supabase import Client
import logging

from app.core.database import get_supabase_admin_client
from app.core.security import get_current_user
from app.services.referral_service import ReferralService, REFERRAL_BONUS_CREDITS
from app.api.v1.schemas.credits import (
    ReferralCodeResponse,
    ReferralValidateRequest,
    ReferralValidateResponse,
    ReferralRedeemRequest,
    ReferralRedeemResponse,
    ReferralStatsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/referrals", tags=["Referrals"])


@router.get(
    "/code",
    response_model=ReferralCodeResponse,
    summary="Get referral code",
    description="Get current user's referral code (generates one if needed)"
)
async def get_referral_code(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Get the current user's referral code.

    If the user doesn't have a code yet, one will be generated.
    The code is an 8-character alphanumeric string.

    Returns:
    - **code**: The user's referral code
    - **uses_count**: How many times the code has been used
    """
    user_id = current_user["id"]

    referral_service = ReferralService(supabase)
    code = await referral_service.get_or_create_referral_code(user_id)

    # Get uses count
    stats = await referral_service.get_referral_stats(user_id)

    return ReferralCodeResponse(
        code=code,
        uses_count=stats["uses_count"]
    )


@router.post(
    "/validate",
    response_model=ReferralValidateResponse,
    summary="Validate referral code",
    description="Check if a referral code is valid for the current user"
)
async def validate_referral_code(
    request: ReferralValidateRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Validate a referral code before redemption.

    This endpoint is useful for real-time validation in the UI
    (e.g., showing a green checkmark when code is valid).

    Validation checks:
    - Code exists
    - Code doesn't belong to the current user
    - Current user hasn't already used a referral code

    Returns:
    - **is_valid**: Whether the code can be used
    - **message**: Validation result message
    - **referrer_name**: Name of the person who shared the code (if valid)
    """
    user_id = current_user["id"]

    referral_service = ReferralService(supabase)
    is_valid, message, referrer_name = await referral_service.validate_referral_code(
        request.code,
        user_id
    )

    return ReferralValidateResponse(
        is_valid=is_valid,
        message=message,
        referrer_name=referrer_name
    )


@router.post(
    "/redeem",
    response_model=ReferralRedeemResponse,
    summary="Redeem referral code",
    description="Redeem a referral code to get bonus credits"
)
async def redeem_referral_code(
    request: ReferralRedeemRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Redeem a referral code.

    When successful:
    - Current user (referee) gets 5 bonus credits
    - Code owner (referrer) gets 5 bonus credits
    - Referral credits expire after 30 days

    Notes:
    - Each user can only use one referral code ever
    - Cannot use your own referral code
    - Maximum 50 referral credits per user

    Returns:
    - **success**: Whether redemption succeeded
    - **message**: Result message
    - **credits_awarded**: Number of credits awarded (if successful)
    """
    user_id = current_user["id"]

    referral_service = ReferralService(supabase)
    success, message = await referral_service.redeem_referral_code(
        request.code,
        user_id
    )

    return ReferralRedeemResponse(
        success=success,
        message=message,
        credits_awarded=REFERRAL_BONUS_CREDITS if success else None
    )


@router.get(
    "/stats",
    response_model=ReferralStatsResponse,
    summary="Get referral statistics",
    description="Get current user's referral statistics"
)
async def get_referral_stats(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Get the current user's referral statistics.

    Returns:
    - **code**: User's referral code
    - **uses_count**: Number of times the code has been used
    - **total_credits_earned**: Total credits earned from referrals
    - **pending_referral_credits**: Credits still available (not expired or used)
    """
    user_id = current_user["id"]

    referral_service = ReferralService(supabase)
    stats = await referral_service.get_referral_stats(user_id)

    return ReferralStatsResponse(**stats)
