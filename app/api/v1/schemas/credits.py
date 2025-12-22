"""
Credits and subscription API schemas
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CreditsResponse(BaseModel):
    """Response for credits endpoint"""
    standard_credits: int = Field(..., description="Weekly standard credits")
    referral_credits: int = Field(..., description="Bonus credits from referrals")
    total_credits: int = Field(..., description="Total available credits")
    is_first_week: bool = Field(..., description="Whether user is in first week (gets 5 credits)")
    next_reset_at: Optional[datetime] = Field(None, description="When credits reset next")
    can_extract: bool = Field(..., description="Whether user can perform extraction")
    is_premium: bool = Field(..., description="Whether user has active subscription")


class CanExtractResponse(BaseModel):
    """Response for extraction check endpoint"""
    can_extract: bool
    reason: str
    credits_remaining: Optional[int] = None


class SubscriptionStatusResponse(BaseModel):
    """Response for subscription status endpoint"""
    status: str = Field(..., description="Subscription status: none, active, trialing, expired, cancelled")
    is_premium: bool
    is_trialing: bool
    product_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    will_renew: bool = False


class ReferralCodeResponse(BaseModel):
    """Response for referral code endpoint"""
    code: str = Field(..., description="User's referral code")
    uses_count: int = Field(..., description="Number of times code has been used")


class ReferralValidateRequest(BaseModel):
    """Request to validate a referral code"""
    code: str = Field(..., min_length=1, max_length=20, description="Referral code to validate")


class ReferralValidateResponse(BaseModel):
    """Response for referral validation"""
    is_valid: bool
    message: str
    referrer_name: Optional[str] = None


class ReferralRedeemRequest(BaseModel):
    """Request to redeem a referral code"""
    code: str = Field(..., min_length=1, max_length=20, description="Referral code to redeem")


class ReferralRedeemResponse(BaseModel):
    """Response for referral redemption"""
    success: bool
    message: str
    credits_awarded: Optional[int] = None


class ReferralStatsResponse(BaseModel):
    """Response for referral statistics"""
    code: str
    uses_count: int
    total_credits_earned: int
    pending_referral_credits: int
