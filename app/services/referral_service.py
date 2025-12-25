"""
Referral service for managing referral codes and redemptions.

Business Rules:
- Each user gets a unique 8-character alphanumeric referral code
- When a new user signs up with a referral code, both get 5 credits
- Referral credits expire after 30 days
- Maximum 50 referral credits per user
- Users can only use one referral code (during onboarding)
"""
from typing import Optional, Tuple, Dict, Any
from supabase import Client
import logging

from app.domain.enums import ReferralSource
from app.services.credit_service import CreditService, REFERRAL_BONUS_CREDITS

logger = logging.getLogger(__name__)


class ReferralService:
    """Service for managing referral codes and redemptions"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.credit_service = CreditService(supabase)

    async def get_or_create_referral_code(self, user_id: str) -> str:
        """
        Get user's referral code, generating one if it doesn't exist.
        Uses database function for atomic generation.
        """
        try:
            # Use the database function
            result = self.supabase.rpc("generate_referral_code", {"p_user_id": user_id}).execute()
            return result.data

        except Exception as e:
            logger.error(f"Error getting/creating referral code for user {user_id}: {e}")
            raise

    async def validate_referral_code(
        self,
        code: str,
        user_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a referral code for a user.
        Returns (is_valid, message, referrer_name).
        """
        try:
            code = code.upper().strip()

            if not code or len(code) != 8:
                return False, "invalid_code_format", None

            # Check if code exists
            response = self.supabase.table("referral_codes").select(
                "*, users:user_id(id, name)"
            ).eq("code", code).execute()

            if not response.data:
                return False, "code_not_found", None

            referral_code = response.data[0]
            referrer_user_id = referral_code["user_id"]
            referrer_name = referral_code.get("users", {}).get("name", "A friend")

            # Check if user is trying to use their own code
            if referrer_user_id == user_id:
                return False, "cannot_use_own_code", None

            # Check if user already used a referral code
            existing = self.supabase.table("referral_redemptions").select("id").eq("referee_user_id", user_id).execute()

            if existing.data:
                return False, "already_used_referral", None

            return True, "valid", referrer_name

        except Exception as e:
            logger.error(f"Error validating referral code {code}: {e}")
            return False, "validation_error", None

    async def redeem_referral_code(
        self,
        code: str,
        referee_user_id: str
    ) -> Tuple[bool, str]:
        """
        Redeem a referral code.
        Awards credits to both referrer and referee.
        Returns (success, message).
        """
        try:
            code = code.upper().strip()

            # Validate first
            is_valid, message, _ = await self.validate_referral_code(code, referee_user_id)

            if not is_valid:
                return False, message

            # Get the referral code record
            response = self.supabase.table("referral_codes").select("*").eq("code", code).execute()

            if not response.data:
                return False, "code_not_found"

            referral_code = response.data[0]
            referrer_user_id = referral_code["user_id"]
            referral_code_id = referral_code["id"]

            # Create redemption record
            self.supabase.table("referral_redemptions").insert({
                "referrer_user_id": referrer_user_id,
                "referee_user_id": referee_user_id,
                "referral_code_id": referral_code_id,
                "credits_awarded": REFERRAL_BONUS_CREDITS
            }).execute()

            # Increment uses count
            self.supabase.table("referral_codes").update({
                "uses_count": referral_code["uses_count"] + 1
            }).eq("id", referral_code_id).execute()

            # Award credits to referee
            await self.credit_service.add_referral_credits(
                user_id=referee_user_id,
                amount=REFERRAL_BONUS_CREDITS,
                source=ReferralSource.REFEREE
            )

            # Award credits to referrer
            await self.credit_service.add_referral_credits(
                user_id=referrer_user_id,
                amount=REFERRAL_BONUS_CREDITS,
                source=ReferralSource.REFERRER
            )

            logger.info(
                f"Referral redeemed: code={code}, referrer={referrer_user_id}, "
                f"referee={referee_user_id}, credits={REFERRAL_BONUS_CREDITS}"
            )

            return True, "success"

        except Exception as e:
            logger.error(f"Error redeeming referral code {code}: {e}")
            return False, "redemption_error"

    async def get_referral_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get referral statistics for a user.
        """
        try:
            # Get or create referral code
            code = await self.get_or_create_referral_code(user_id)

            # Get code info with uses count
            code_response = self.supabase.table("referral_codes").select("*").eq("user_id", user_id).execute()

            uses_count = code_response.data[0]["uses_count"] if code_response.data else 0

            # Calculate total credits earned from referrals
            total_earned = uses_count * REFERRAL_BONUS_CREDITS

            # Get current valid referral credits
            pending_credits = await self.credit_service._get_valid_referral_credits(user_id)

            return {
                "code": code,
                "uses_count": uses_count,
                "total_credits_earned": total_earned,
                "pending_referral_credits": pending_credits
            }

        except Exception as e:
            logger.error(f"Error getting referral stats for user {user_id}: {e}")
            raise

    async def has_used_referral(self, user_id: str) -> bool:
        """Check if user has already used a referral code"""
        try:
            response = self.supabase.table("referral_redemptions").select("id").eq("referee_user_id", user_id).execute()

            return bool(response.data)

        except Exception as e:
            logger.error(f"Error checking referral usage for user {user_id}: {e}")
            return False
