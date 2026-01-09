"""
Credit service for managing user extraction credits.

Business Rules:
- Premium users: Unlimited extractions (no credits needed)
- Free users (first week): 5 credits/week
- Free users (after first week): 3 credits/week
- Credits reset weekly (Monday 00:00 UTC)
- Unused standard credits don't carry over
- Referral credits persist separately (30-day expiry, max 50)
- Use standard credits first, then referral credits
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from supabase import Client
import logging

from app.domain.enums import CreditType, CreditTransactionReason, ReferralSource

logger = logging.getLogger(__name__)

# Constants
FIRST_WEEK_CREDITS = 5
STANDARD_WEEKLY_CREDITS = 3
REFERRAL_BONUS_CREDITS = 5
REFERRAL_EXPIRY_DAYS = 30
MAX_REFERRAL_CREDITS = 50


class CreditService:
    """Service for managing user extraction credits"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def get_or_create_user_credits(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's credit record, creating one if it doesn't exist.
        Uses the database function for atomic initialization.
        """
        try:
            # Try to get existing credits first
            response = self.supabase.table("user_credits").select("*").eq("user_id", user_id).execute()

            if response.data:
                return response.data[0]

            # Initialize new credits using database function
            result = self.supabase.rpc("initialize_user_credits", {"p_user_id": user_id}).execute()
            return result.data

        except Exception as e:
            logger.error(f"Error getting/creating credits for user {user_id}: {e}")
            raise

    async def get_credits_response(self, user_id: str, is_premium: bool = False) -> Dict[str, Any]:
        """
        Get formatted credits response for API.
        Includes lazy reset check.
        """
        # Premium users don't need credits
        if is_premium:
            return {
                "standard_credits": 0,
                "referral_credits": 0,
                "total_credits": 0,
                "is_first_week": False,
                "next_reset_at": None,
                "can_extract": True,
                "is_premium": True,
            }

        # Get or create credits
        credits = await self.get_or_create_user_credits(user_id)

        # Check and perform lazy reset if needed
        credits = await self._check_and_reset_if_needed(user_id, credits)

        # Expire old referral credits and recalculate
        await self._expire_referral_credits(user_id)
        referral_credits = await self._get_valid_referral_credits(user_id)

        is_first_week = credits.get("first_week_ends_at") is None or (
            datetime.fromisoformat(credits["first_week_ends_at"].replace("Z", "+00:00")) > datetime.now(timezone.utc)
        )

        total_credits = credits["standard_credits"] + referral_credits

        return {
            "standard_credits": credits["standard_credits"],
            "referral_credits": referral_credits,
            "total_credits": total_credits,
            "is_first_week": is_first_week,
            "next_reset_at": credits.get("credits_reset_at"),
            "can_extract": total_credits > 0,
            "is_premium": False,
        }

    async def can_extract(self, user_id: str, is_premium: bool = False) -> Tuple[bool, str]:
        """
        Check if user can perform an extraction.
        Returns (allowed, reason).
        """
        if is_premium:
            return True, "premium"

        # Get credits with lazy reset
        credits = await self.get_or_create_user_credits(user_id)
        credits = await self._check_and_reset_if_needed(user_id, credits)

        # Expire old referral credits
        await self._expire_referral_credits(user_id)

        # Get current valid referral credits
        referral_credits = await self._get_valid_referral_credits(user_id)

        total = credits["standard_credits"] + referral_credits

        if total > 0:
            return True, f"{total} credits available"

        return False, "no_credits"

    async def deduct_credit(
        self,
        user_id: str,
        extraction_job_id: Optional[str] = None,
        is_premium: bool = False
    ) -> bool:
        """
        Deduct one credit for an extraction.
        Uses standard credits first, then referral credits.
        Returns True if successful.
        """
        if is_premium:
            # Premium users don't use credits
            return True

        try:
            # Get credits with lazy reset
            credits = await self.get_or_create_user_credits(user_id)
            credits = await self._check_and_reset_if_needed(user_id, credits)

            # Expire old referral credits first
            await self._expire_referral_credits(user_id)

            # Try standard credits first
            if credits["standard_credits"] > 0:
                new_standard = credits["standard_credits"] - 1
                self.supabase.table("user_credits").update({
                    "standard_credits": new_standard,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("user_id", user_id).execute()

                # Log transaction
                await self._log_transaction(
                    user_id=user_id,
                    amount=-1,
                    credit_type=CreditType.STANDARD,
                    reason=CreditTransactionReason.EXTRACTION,
                    extraction_job_id=extraction_job_id,
                    balance_after=new_standard
                )
                return True

            # Try referral credits (oldest first)
            referral_grant = await self._get_oldest_valid_referral_grant(user_id)
            if referral_grant:
                new_remaining = referral_grant["remaining"] - 1

                if new_remaining > 0:
                    self.supabase.table("referral_credit_grants").update({
                        "remaining": new_remaining
                    }).eq("id", referral_grant["id"]).execute()
                else:
                    # Delete depleted grant
                    self.supabase.table("referral_credit_grants").delete().eq("id", referral_grant["id"]).execute()

                # Update user_credits.referral_credits total
                await self._update_referral_credits_total(user_id)

                # Log transaction
                referral_total = await self._get_valid_referral_credits(user_id)
                await self._log_transaction(
                    user_id=user_id,
                    amount=-1,
                    credit_type=CreditType.REFERRAL,
                    reason=CreditTransactionReason.EXTRACTION,
                    extraction_job_id=extraction_job_id,
                    balance_after=referral_total
                )
                return True

            logger.warning(f"User {user_id} attempted extraction with no credits")
            return False

        except Exception as e:
            logger.error(f"Error deducting credit for user {user_id}: {e}")
            raise

    async def add_referral_credits(
        self,
        user_id: str,
        amount: int,
        source: ReferralSource
    ) -> bool:
        """
        Add referral credits to a user.
        Respects the MAX_REFERRAL_CREDITS cap.
        """
        try:
            # Check current referral credits total
            current_total = await self._get_valid_referral_credits(user_id)

            if current_total >= MAX_REFERRAL_CREDITS:
                logger.info(f"User {user_id} at referral credits cap ({MAX_REFERRAL_CREDITS})")
                return False

            # Cap the amount to not exceed max
            amount_to_add = min(amount, MAX_REFERRAL_CREDITS - current_total)

            if amount_to_add <= 0:
                return False

            # Create referral credit grant
            expires_at = datetime.now(timezone.utc) + timedelta(days=REFERRAL_EXPIRY_DAYS)

            self.supabase.table("referral_credit_grants").insert({
                "user_id": user_id,
                "amount": amount_to_add,
                "remaining": amount_to_add,
                "source": source.value,
                "expires_at": expires_at.isoformat()
            }).execute()

            # Update user_credits total
            await self._update_referral_credits_total(user_id)

            # Log transaction
            new_total = await self._get_valid_referral_credits(user_id)
            await self._log_transaction(
                user_id=user_id,
                amount=amount_to_add,
                credit_type=CreditType.REFERRAL,
                reason=CreditTransactionReason.REFERRAL_BONUS,
                balance_after=new_total
            )

            return True

        except Exception as e:
            logger.error(f"Error adding referral credits for user {user_id}: {e}")
            raise

    async def _check_and_reset_if_needed(
        self,
        user_id: str,
        credits: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if weekly reset is needed and perform it.
        Returns updated credits record.
        """
        reset_at_str = credits.get("credits_reset_at")
        if not reset_at_str:
            return credits

        reset_at = datetime.fromisoformat(reset_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        if now >= reset_at:
            # Time to reset!
            first_week_ends_at = credits.get("first_week_ends_at")

            # Determine credit amount based on first week status
            if first_week_ends_at:
                first_week_ends = datetime.fromisoformat(first_week_ends_at.replace("Z", "+00:00"))
                is_first_week = now < first_week_ends
            else:
                # First week hasn't been set - this is their first reset
                is_first_week = True
                first_week_ends_at = (now + timedelta(days=7)).isoformat()

            new_credits = FIRST_WEEK_CREDITS if is_first_week else STANDARD_WEEKLY_CREDITS

            # Calculate next Monday 00:00 UTC
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_reset = (now + timedelta(days=days_until_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # Update credits
            update_data = {
                "standard_credits": new_credits,
                "credits_reset_at": next_reset.isoformat(),
                "updated_at": now.isoformat()
            }

            if not credits.get("first_week_ends_at"):
                update_data["first_week_ends_at"] = first_week_ends_at

            response = self.supabase.table("user_credits").update(update_data).eq("user_id", user_id).execute()

            if response.data:
                # Log the reset transaction
                await self._log_transaction(
                    user_id=user_id,
                    amount=new_credits,
                    credit_type=CreditType.STANDARD,
                    reason=CreditTransactionReason.WEEKLY_RESET,
                    balance_after=new_credits
                )
                return response.data[0]

        return credits

    async def _expire_referral_credits(self, user_id: str) -> int:
        """
        Expire any referral credit grants past their expiry date.
        Returns number of credits expired.
        """
        try:
            now = datetime.now(timezone.utc).isoformat()

            # Get expired grants
            response = self.supabase.table("referral_credit_grants").select("*").eq("user_id", user_id).lt("expires_at", now).gt("remaining", 0).execute()

            expired_grants = response.data or []
            total_expired = sum(g["remaining"] for g in expired_grants)

            if total_expired > 0:
                # Delete expired grants
                self.supabase.table("referral_credit_grants").delete().eq("user_id", user_id).lt("expires_at", now).execute()

                # Update user_credits total
                await self._update_referral_credits_total(user_id)

                # Log expiration
                await self._log_transaction(
                    user_id=user_id,
                    amount=-total_expired,
                    credit_type=CreditType.REFERRAL,
                    reason=CreditTransactionReason.EXPIRED,
                    balance_after=await self._get_valid_referral_credits(user_id)
                )

            return total_expired

        except Exception as e:
            logger.error(f"Error expiring referral credits for user {user_id}: {e}")
            return 0

    async def _get_valid_referral_credits(self, user_id: str) -> int:
        """Get sum of all non-expired referral credits"""
        try:
            now = datetime.now(timezone.utc).isoformat()

            response = self.supabase.table("referral_credit_grants").select("remaining").eq("user_id", user_id).gt("expires_at", now).gt("remaining", 0).execute()

            return sum(g["remaining"] for g in (response.data or []))

        except Exception as e:
            logger.error(f"Error getting referral credits for user {user_id}: {e}")
            return 0

    async def _get_oldest_valid_referral_grant(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the oldest non-expired referral grant with remaining credits"""
        try:
            now = datetime.now(timezone.utc).isoformat()

            response = self.supabase.table("referral_credit_grants").select("*").eq("user_id", user_id).gt("expires_at", now).gt("remaining", 0).order("created_at", desc=False).limit(1).execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error getting oldest referral grant for user {user_id}: {e}")
            return None

    async def _update_referral_credits_total(self, user_id: str) -> None:
        """Update the referral_credits total in user_credits table"""
        try:
            total = await self._get_valid_referral_credits(user_id)

            self.supabase.table("user_credits").update({
                "referral_credits": total,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", user_id).execute()

        except Exception as e:
            logger.error(f"Error updating referral credits total for user {user_id}: {e}")

    async def _log_transaction(
        self,
        user_id: str,
        amount: int,
        credit_type: CreditType,
        reason: CreditTransactionReason,
        balance_after: int,
        extraction_job_id: Optional[str] = None
    ) -> None:
        """Log a credit transaction for auditing"""
        try:
            self.supabase.table("credit_transactions").insert({
                "user_id": user_id,
                "amount": amount,
                "credit_type": credit_type.value,
                "reason": reason.value,
                "extraction_job_id": extraction_job_id,
                "balance_after": balance_after
            }).execute()

        except Exception as e:
            # Don't fail the main operation if logging fails
            logger.error(f"Error logging credit transaction: {e}")
