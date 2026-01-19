"""
Moderation service for admin actions on reports, users, and recipes.

Handles:
- Reviewing and resolving content reports
- Reviewing extraction feedback
- User warnings, suspensions, and bans
- Recipe hiding/unhiding
- Audit logging of all actions
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from supabase import Client
import logging

from app.domain.enums import (
    ReportStatus,
    UserModerationStatus,
    ModerationActionType,
)
from app.repositories.content_report_repository import ContentReportRepository
from app.repositories.extraction_feedback_repository import ExtractionFeedbackRepository
from app.repositories.user_moderation_repository import UserModerationRepository
from app.repositories.moderation_action_repository import (
    ModerationActionRepository,
    UserWarningRepository,
)

logger = logging.getLogger(__name__)

# Constants
RELIABILITY_VALID_REPORT_BONUS = 5  # Points added for valid reports
RELIABILITY_FALSE_REPORT_PENALTY = -15  # Points subtracted for false reports
AUTO_SUSPEND_WARNING_THRESHOLD = 3  # Warnings before auto-suspension
AUTO_BAN_WARNING_THRESHOLD = 5  # Warnings before considering ban


class ModerationService:
    """Service for admin moderation actions"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.content_report_repo = ContentReportRepository(supabase)
        self.extraction_feedback_repo = ExtractionFeedbackRepository(supabase)
        self.user_moderation_repo = UserModerationRepository(supabase)
        self.moderation_action_repo = ModerationActionRepository(supabase)
        self.user_warning_repo = UserWarningRepository(supabase)

    # =========================================================================
    # CONTENT REPORT MANAGEMENT
    # =========================================================================

    async def get_report_queue(
        self,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        min_priority: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get pending content reports for review.

        Args:
            status: Filter by status (default: pending)
            reason: Filter by report reason
            min_priority: Minimum priority threshold
            limit: Maximum number of reports to return
            offset: Number of reports to skip

        Returns:
            List of reports with recipe and reporter info
        """
        if status is None:
            status = ReportStatus.PENDING.value

        return await self.content_report_repo.get_pending_reports(
            limit=limit,
            offset=offset,
            reason=reason,
            min_priority=min_priority
        )

    async def get_report_details(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full details of a content report.

        Args:
            report_id: ID of the report

        Returns:
            Report with full recipe and user details
        """
        return await self.content_report_repo.get_report_with_details(report_id)

    async def dismiss_report(
        self,
        moderator_id: str,
        report_id: str,
        reason: str,
        notes: Optional[str] = None,
        is_false_report: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Dismiss a content report as invalid or already addressed.

        Args:
            moderator_id: ID of the moderator
            report_id: ID of the report to dismiss
            reason: Reason for dismissal
            notes: Optional internal notes
            is_false_report: Whether this was a false/abusive report

        Returns:
            Tuple of (updated report, error message if any)
        """
        try:
            # Get report details
            report = await self.content_report_repo.get_by_id(report_id)
            if not report:
                return None, "Report not found"

            # Update report status
            updated_report = await self.content_report_repo.update_status(
                report_id=report_id,
                status=ReportStatus.RESOLVED.value,
                resolved_by=moderator_id,
                resolution_notes=notes
            )

            # Log the action
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.DISMISS_REPORT.value,
                reason=reason,
                content_report_id=report_id,
                notes=notes
            )

            # If false report, penalize reporter reliability
            if is_false_report:
                reporter_id = report.get("reporter_user_id")
                if reporter_id:
                    await self.user_moderation_repo.adjust_reliability_score(
                        reporter_id,
                        RELIABILITY_FALSE_REPORT_PENALTY
                    )
                    await self.user_moderation_repo.increment_false_report_count(reporter_id)

            logger.info(f"Report {report_id} dismissed by moderator {moderator_id}")
            return updated_report, None

        except Exception as e:
            logger.error(f"Error dismissing report: {str(e)}")
            return None, "An error occurred while dismissing the report"

    async def take_action_on_report(
        self,
        moderator_id: str,
        report_id: str,
        action: str,
        reason: str,
        notes: Optional[str] = None,
        suspension_days: Optional[int] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Take moderation action based on a content report.

        Args:
            moderator_id: ID of the moderator
            report_id: ID of the report
            action: Action to take (hide_recipe, warn_user, suspend_user, ban_user)
            reason: Reason for the action
            notes: Optional internal notes
            suspension_days: Days to suspend (if suspending)

        Returns:
            Tuple of (result, error message if any)
        """
        try:
            # Get report details
            report = await self.content_report_repo.get_report_with_details(report_id)
            if not report:
                return None, "Report not found"

            recipe = report.get("recipes")
            recipe_id = recipe.get("id") if recipe else None
            recipe_owner_id = recipe.get("created_by") if recipe else None

            result = None

            if action == "hide_recipe" and recipe_id:
                result, error = await self.hide_recipe(
                    moderator_id=moderator_id,
                    recipe_id=recipe_id,
                    reason=reason,
                    report_id=report_id
                )
                if error:
                    return None, error

            elif action == "warn_user" and recipe_owner_id:
                result, error = await self.warn_user(
                    moderator_id=moderator_id,
                    user_id=recipe_owner_id,
                    reason=reason,
                    report_id=report_id,
                    recipe_id=recipe_id
                )
                if error:
                    return None, error

            elif action == "suspend_user" and recipe_owner_id:
                result, error = await self.suspend_user(
                    moderator_id=moderator_id,
                    user_id=recipe_owner_id,
                    duration_days=suspension_days or 7,
                    reason=reason
                )
                if error:
                    return None, error

            elif action == "ban_user" and recipe_owner_id:
                result, error = await self.ban_user(
                    moderator_id=moderator_id,
                    user_id=recipe_owner_id,
                    reason=reason
                )
                if error:
                    return None, error

            else:
                return None, f"Invalid action: {action}"

            # Update report status
            await self.content_report_repo.update_status(
                report_id=report_id,
                status=ReportStatus.RESOLVED.value,
                resolved_by=moderator_id,
                resolution_notes=f"Action taken: {action}. {notes or ''}"
            )

            # Reward reporter for valid report
            reporter_id = report.get("reporter_user_id")
            if reporter_id:
                await self.user_moderation_repo.adjust_reliability_score(
                    reporter_id,
                    RELIABILITY_VALID_REPORT_BONUS
                )

            return result, None

        except Exception as e:
            logger.error(f"Error taking action on report: {str(e)}")
            return None, "An error occurred while processing the action"

    # =========================================================================
    # EXTRACTION FEEDBACK MANAGEMENT
    # =========================================================================

    async def get_feedback_queue(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get pending extraction feedback for review.

        Args:
            status: Filter by status (default: pending)
            category: Filter by feedback category
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            List of feedback with recipe and user info
        """
        return await self.extraction_feedback_repo.get_pending_feedback(
            limit=limit,
            offset=offset,
            category=category
        )

    async def get_feedback_details(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full details of extraction feedback.

        Args:
            feedback_id: ID of the feedback

        Returns:
            Feedback with full recipe and user details
        """
        return await self.extraction_feedback_repo.get_feedback_with_details(feedback_id)

    async def resolve_feedback(
        self,
        moderator_id: str,
        feedback_id: str,
        resolution_notes: Optional[str] = None,
        was_helpful: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Resolve extraction feedback.

        Args:
            moderator_id: ID of the moderator
            feedback_id: ID of the feedback
            resolution_notes: Notes about the resolution
            was_helpful: Whether feedback was helpful for improvement

        Returns:
            Tuple of (updated feedback, error message if any)
        """
        try:
            feedback = await self.extraction_feedback_repo.resolve_feedback(
                feedback_id=feedback_id,
                resolved_by=moderator_id,
                resolution_notes=resolution_notes,
                was_helpful=was_helpful
            )

            if not feedback:
                return None, "Feedback not found"

            # Log the action
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.RESOLVE_FEEDBACK.value,
                reason=f"Feedback resolved. Helpful: {was_helpful}",
                extraction_feedback_id=feedback_id,
                notes=resolution_notes
            )

            return feedback, None

        except Exception as e:
            logger.error(f"Error resolving feedback: {str(e)}")
            return None, "An error occurred while resolving feedback"

    # =========================================================================
    # RECIPE MODERATION
    # =========================================================================

    async def hide_recipe(
        self,
        moderator_id: str,
        recipe_id: str,
        reason: str,
        report_id: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Hide a recipe from public view.

        Args:
            moderator_id: ID of the moderator
            recipe_id: ID of the recipe to hide
            reason: Reason for hiding
            report_id: Optional related report ID

        Returns:
            Tuple of (updated recipe, error message if any)
        """
        try:
            # Update recipe
            response = self.supabase.table("recipes")\
                .update({
                    "is_hidden": True,
                    "hidden_at": datetime.now(timezone.utc).isoformat(),
                    "hidden_reason": reason
                })\
                .eq("id", recipe_id)\
                .execute()

            if not response.data:
                return None, "Recipe not found"

            # Log the action
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.HIDE_RECIPE.value,
                reason=reason,
                target_recipe_id=recipe_id,
                content_report_id=report_id
            )

            logger.info(f"Recipe {recipe_id} hidden by moderator {moderator_id}")
            return response.data[0], None

        except Exception as e:
            logger.error(f"Error hiding recipe: {str(e)}")
            return None, "An error occurred while hiding the recipe"

    async def unhide_recipe(
        self,
        moderator_id: str,
        recipe_id: str,
        reason: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Restore a hidden recipe to public view.

        Args:
            moderator_id: ID of the moderator
            recipe_id: ID of the recipe to unhide
            reason: Reason for unhiding

        Returns:
            Tuple of (updated recipe, error message if any)
        """
        try:
            # Update recipe
            response = self.supabase.table("recipes")\
                .update({
                    "is_hidden": False,
                    "hidden_at": None,
                    "hidden_reason": None
                })\
                .eq("id", recipe_id)\
                .execute()

            if not response.data:
                return None, "Recipe not found"

            # Log the action
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.UNHIDE_RECIPE.value,
                reason=reason,
                target_recipe_id=recipe_id
            )

            logger.info(f"Recipe {recipe_id} unhidden by moderator {moderator_id}")
            return response.data[0], None

        except Exception as e:
            logger.error(f"Error unhiding recipe: {str(e)}")
            return None, "An error occurred while unhiding the recipe"

    # =========================================================================
    # USER MODERATION
    # =========================================================================

    async def warn_user(
        self,
        moderator_id: str,
        user_id: str,
        reason: str,
        report_id: Optional[str] = None,
        recipe_id: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Issue a warning to a user.

        Args:
            moderator_id: ID of the moderator
            user_id: ID of the user to warn
            reason: Reason for the warning
            report_id: Optional related report ID
            recipe_id: Optional related recipe ID

        Returns:
            Tuple of (warning record, error message if any)
        """
        try:
            # Create warning
            warning = await self.user_warning_repo.create_warning(
                user_id=user_id,
                issued_by=moderator_id,
                reason=reason,
                content_report_id=report_id,
                recipe_id=recipe_id
            )

            if not warning:
                return None, "Failed to create warning"

            # Increment warning count
            moderation = await self.user_moderation_repo.increment_warning_count(user_id)

            # Log the action
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.WARN_USER.value,
                reason=reason,
                target_user_id=user_id,
                content_report_id=report_id
            )

            # Check for auto-suspension
            warning_count = moderation.get("warning_count", 0) if moderation else 0
            if warning_count >= AUTO_SUSPEND_WARNING_THRESHOLD:
                logger.info(f"User {user_id} reached {warning_count} warnings, consider suspension")

            logger.info(f"User {user_id} warned by moderator {moderator_id}")
            return warning, None

        except Exception as e:
            logger.error(f"Error warning user: {str(e)}")
            return None, "An error occurred while issuing the warning"

    async def suspend_user(
        self,
        moderator_id: str,
        user_id: str,
        duration_days: int,
        reason: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Temporarily suspend a user using Supabase's native ban.

        Args:
            moderator_id: ID of the moderator
            user_id: ID of the user to suspend
            duration_days: Duration of suspension in days
            reason: Reason for suspension

        Returns:
            Tuple of (result dict, error message if any)
        """
        try:
            # Use Supabase's native ban with duration
            # Convert days to hours for Supabase (supports formats like "24h", "168h")
            duration_hours = duration_days * 24
            self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"ban_duration": f"{duration_hours}h"}
            )

            # Log the action for audit trail
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.SUSPEND_USER.value,
                reason=reason,
                target_user_id=user_id,
                duration_days=duration_days
            )

            logger.info(f"User {user_id} suspended for {duration_days} days by moderator {moderator_id}")
            return {"user_id": user_id, "suspended_days": duration_days}, None

        except Exception as e:
            logger.error(f"Error suspending user: {str(e)}")
            return None, "An error occurred while suspending the user"

    async def unsuspend_user(
        self,
        moderator_id: str,
        user_id: str,
        reason: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Remove suspension from a user using Supabase's native unban.

        Args:
            moderator_id: ID of the moderator
            user_id: ID of the user to unsuspend
            reason: Reason for unsuspension

        Returns:
            Tuple of (result dict, error message if any)
        """
        try:
            # Remove Supabase ban
            self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"ban_duration": "none"}
            )

            # Log the action
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.UNSUSPEND_USER.value,
                reason=reason,
                target_user_id=user_id
            )

            logger.info(f"User {user_id} unsuspended by moderator {moderator_id}")
            return {"user_id": user_id, "unsuspended": True}, None

        except Exception as e:
            logger.error(f"Error unsuspending user: {str(e)}")
            return None, "An error occurred while unsuspending the user"

    async def ban_user(
        self,
        moderator_id: str,
        user_id: str,
        reason: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Permanently ban a user using Supabase's native ban.

        Args:
            moderator_id: ID of the moderator
            user_id: ID of the user to ban
            reason: Reason for ban

        Returns:
            Tuple of (result dict, error message if any)
        """
        try:
            # Use Supabase's native ban with ~100 year duration (permanent)
            self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"ban_duration": "876000h"}  # ~100 years
            )

            # Hide all user's public recipes
            self.supabase.table("recipes")\
                .update({
                    "is_hidden": True,
                    "hidden_at": datetime.now(timezone.utc).isoformat(),
                    "hidden_reason": f"User banned: {reason}"
                })\
                .eq("created_by", user_id)\
                .eq("is_public", True)\
                .execute()

            # Log the action
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.BAN_USER.value,
                reason=reason,
                target_user_id=user_id
            )

            logger.info(f"User {user_id} banned by moderator {moderator_id}")
            return {"user_id": user_id, "banned": True}, None

        except Exception as e:
            logger.error(f"Error banning user: {str(e)}")
            return None, "An error occurred while banning the user"

    async def unban_user(
        self,
        moderator_id: str,
        user_id: str,
        reason: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Remove ban from a user using Supabase's native unban.

        Args:
            moderator_id: ID of the moderator
            user_id: ID of the user to unban
            reason: Reason for unban

        Returns:
            Tuple of (result dict, error message if any)
        """
        try:
            # Remove Supabase ban
            self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"ban_duration": "none"}
            )

            # Log the action
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type=ModerationActionType.UNBAN_USER.value,
                reason=reason,
                target_user_id=user_id
            )

            logger.info(f"User {user_id} unbanned by moderator {moderator_id}")
            return {"user_id": user_id, "unbanned": True}, None

        except Exception as e:
            logger.error(f"Error unbanning user: {str(e)}")
            return None, "An error occurred while unbanning the user"

    # =========================================================================
    # USER HISTORY & STATISTICS
    # =========================================================================

    async def get_user_moderation_details(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get complete moderation details for a user.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with moderation status, warnings, and action history
        """
        try:
            # Get moderation status
            moderation = await self.user_moderation_repo.get_or_create(user_id)

            # Get warnings
            warnings = await self.user_warning_repo.get_user_warnings(user_id, limit=20)

            # Get actions targeting this user
            actions = await self.moderation_action_repo.get_actions_for_user(user_id, limit=20)

            # Get user info
            user_response = self.supabase.table("users")\
                .select("id, name, avatar_url, created_at")\
                .eq("id", user_id)\
                .single()\
                .execute()

            return {
                "user": user_response.data,
                "moderation": moderation,
                "warnings": warnings,
                "actions": actions
            }

        except Exception as e:
            logger.error(f"Error getting user moderation details: {str(e)}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall moderation statistics.

        Returns:
            Dictionary with report, feedback, and user statistics
        """
        try:
            report_stats = await self.content_report_repo.get_report_statistics()
            feedback_stats = await self.extraction_feedback_repo.get_feedback_statistics()
            user_stats = await self.user_moderation_repo.get_moderation_statistics()
            action_stats = await self.moderation_action_repo.get_action_statistics(days=30)

            return {
                "reports": report_stats,
                "feedback": feedback_stats,
                "users": user_stats,
                "actions": action_stats
            }

        except Exception as e:
            logger.error(f"Error getting moderation statistics: {str(e)}")
            raise

    # =========================================================================
    # USER LIST & ENHANCED DETAILS
    # =========================================================================

    async def get_users_list(
        self,
        status: Optional[str] = None,
        is_premium: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get paginated list of users with moderation and subscription info.

        Args:
            status: Filter by moderation status (good_standing, warned, suspended, banned)
            is_premium: Filter by premium subscription status
            search: Search by name or email (name only - email search requires auth admin)
            sort_by: Field to sort by (created_at, name)
            sort_order: asc or desc
            limit: Max users to return
            offset: Pagination offset

        Returns:
            Dictionary with users list and total count
        """
        try:
            # Build query for public.users table
            # Note: email and last_sign_in_at are in auth.users, not public.users
            query = self.supabase.table("users")\
                .select(
                    "id, name, avatar_url, created_at",
                    count="exact"
                )

            # Apply search filter (name only - email is in auth.users)
            if search:
                query = query.ilike("name", f"%{search}%")

            # Apply sorting (only fields in public.users)
            if sort_by in ["created_at", "name"]:
                query = query.order(sort_by, desc=(sort_order == "desc"))
            else:
                query = query.order("created_at", desc=(sort_order == "desc"))

            # Apply pagination
            query = query.limit(limit).offset(offset)

            response = query.execute()

            # Get moderation and subscription data for these users
            user_ids = [u["id"] for u in (response.data or [])]

            if not user_ids:
                return {"users": [], "total": 0}

            # Get auth user data (email, last_sign_in_at) via admin API
            auth_by_user: Dict[str, dict] = {}
            for uid in user_ids:
                try:
                    auth_user = self.supabase.auth.admin.get_user_by_id(uid)
                    if auth_user and auth_user.user:
                        auth_by_user[uid] = {
                            "email": auth_user.user.email,
                            "last_sign_in_at": auth_user.user.last_sign_in_at
                        }
                except Exception as auth_err:
                    logger.warning(f"Could not fetch auth data for user {uid}: {auth_err}")

            # Get moderation records
            mod_response = self.supabase.table("user_moderation")\
                .select("*")\
                .in_("user_id", user_ids)\
                .execute()
            mod_by_user = {m["user_id"]: m for m in (mod_response.data or [])}

            # Get subscription records
            sub_response = self.supabase.table("user_subscriptions")\
                .select("user_id, is_active, expires_at, is_trial")\
                .in_("user_id", user_ids)\
                .execute()
            sub_by_user = {s["user_id"]: s for s in (sub_response.data or [])}

            # Get reports submitted by each user
            reports_response = self.supabase.table("content_reports")\
                .select("reporter_user_id")\
                .in_("reporter_user_id", user_ids)\
                .execute()
            reports_by_user: Dict[str, int] = {}
            for r in (reports_response.data or []):
                uid = r["reporter_user_id"]
                reports_by_user[uid] = reports_by_user.get(uid, 0) + 1

            # Transform data
            users = []
            for user in response.data or []:
                user_id = user["id"]
                auth_data = auth_by_user.get(user_id, {})
                moderation = mod_by_user.get(user_id, {})
                subscription = sub_by_user.get(user_id, {})

                user_item = {
                    "id": user_id,
                    "name": user.get("name"),
                    "email": auth_data.get("email"),
                    "avatar_url": user.get("avatar_url"),
                    "created_at": user["created_at"],
                    "last_sign_in_at": auth_data.get("last_sign_in_at"),
                    "moderation_status": moderation.get("status", "good_standing"),
                    "warning_count": moderation.get("warning_count", 0),
                    "report_count": moderation.get("report_count", 0),
                    "reports_submitted": reports_by_user.get(user_id, 0),
                    "false_report_count": moderation.get("false_report_count", 0),
                    "reporter_reliability_score": moderation.get("reporter_reliability_score", 100) / 100.0,
                    "is_premium": subscription.get("is_active", False),
                    "subscription_expires_at": subscription.get("expires_at"),
                    "is_trial": subscription.get("is_trial", False),
                }

                # Apply status filter (after fetching since we need to join)
                if status and user_item["moderation_status"] != status:
                    continue

                # Apply premium filter
                if is_premium is not None and user_item["is_premium"] != is_premium:
                    continue

                users.append(user_item)

            return {
                "users": users,
                "total": response.count or len(users)
            }

        except Exception as e:
            logger.error(f"Error getting users list: {str(e)}")
            raise

    async def get_user_moderation_details_enhanced(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get complete moderation details for a user including feedback and subscription.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with moderation status, warnings, actions, feedback, and subscription
        """
        try:
            # Get base moderation details
            base_details = await self.get_user_moderation_details(user_id)

            # Get user's extraction feedback
            feedback_response = self.supabase.table("extraction_feedback")\
                .select("*, recipes(id, title, image_url)")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()

            # Get subscription info
            sub_response = self.supabase.table("user_subscriptions")\
                .select("is_active, product_id, expires_at, is_trial")\
                .eq("user_id", user_id)\
                .execute()
            subscription = sub_response.data[0] if sub_response.data else {}

            # Get user created_at from public.users
            user_response = self.supabase.table("users")\
                .select("created_at")\
                .eq("id", user_id)\
                .single()\
                .execute()
            user_data = user_response.data or {}

            # Get email and last_sign_in_at from auth.users via admin API
            auth_data = {}
            try:
                auth_user = self.supabase.auth.admin.get_user_by_id(user_id)
                if auth_user and auth_user.user:
                    auth_data = {
                        "email": auth_user.user.email,
                        "last_sign_in_at": auth_user.user.last_sign_in_at
                    }
            except Exception as auth_err:
                logger.warning(f"Could not fetch auth data for user {user_id}: {auth_err}")

            # Count reports submitted by this user
            reports_count_response = self.supabase.table("content_reports")\
                .select("id", count="exact")\
                .eq("reporter_user_id", user_id)\
                .execute()

            return {
                **base_details,
                "email": auth_data.get("email"),
                "created_at": user_data.get("created_at"),
                "last_sign_in_at": auth_data.get("last_sign_in_at"),
                "feedback": feedback_response.data or [],
                "reports_submitted": reports_count_response.count or 0,
                "is_premium": subscription.get("is_active", False),
                "subscription_product_id": subscription.get("product_id"),
                "subscription_expires_at": subscription.get("expires_at"),
                "is_trial": subscription.get("is_trial", False),
            }

        except Exception as e:
            logger.error(f"Error getting enhanced user moderation details: {str(e)}")
            raise

    async def delete_user(
        self,
        moderator_id: str,
        user_id: str,
        reason: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Delete a user account (admin action).

        Transfers video-extracted recipes to system account,
        deletes personal recipes, anonymizes contributor records.

        Args:
            moderator_id: ID of the moderator performing the action
            user_id: ID of the user to delete
            reason: Reason for deletion

        Returns:
            Tuple of (result dict, error message if any)
        """
        try:
            # System account ID for transferring video recipes
            SYSTEM_ACCOUNT_ID = "00000000-0000-0000-0000-000000000000"

            logger.info(f"Admin {moderator_id} starting account deletion for user {user_id}")

            # Step 1: Find video-extracted recipes owned by this user
            video_recipes_result = self.supabase.table("recipes")\
                .select("id")\
                .eq("created_by", user_id)\
                .eq("source_type", "video")\
                .execute()

            video_recipe_ids = []
            if video_recipes_result.data:
                video_recipe_ids = [r["id"] for r in video_recipes_result.data]

            # Step 2: Transfer video-extracted recipes to system account
            if video_recipe_ids:
                system_account = self.supabase.table("users")\
                    .select("id")\
                    .eq("id", SYSTEM_ACCOUNT_ID)\
                    .execute()

                if system_account.data:
                    self.supabase.table("recipes")\
                        .update({"created_by": SYSTEM_ACCOUNT_ID})\
                        .in_("id", video_recipe_ids)\
                        .execute()
                    logger.info(f"Transferred {len(video_recipe_ids)} video-extracted recipes to system account")

            # Step 3: Anonymize contributor records
            self.supabase.table("recipe_contributors")\
                .update({"display_name": "[Deleted User]", "user_id": None})\
                .eq("user_id", user_id)\
                .execute()

            # Step 4: Clean up storage
            for bucket_name in ["recipe-images", "cooking-events"]:
                try:
                    files = self.supabase.storage.from_(bucket_name).list(path=user_id)
                    if files:
                        file_paths = [f"{user_id}/{f['name']}" for f in files]
                        self.supabase.storage.from_(bucket_name).remove(file_paths)
                        logger.info(f"Deleted {len(file_paths)} files from {bucket_name}/{user_id}")
                except Exception as storage_error:
                    logger.warning(f"Storage cleanup error for {bucket_name}/{user_id}: {storage_error}")

            # Step 5: Log the moderation action before deleting user
            await self.moderation_action_repo.log_action(
                moderator_id=moderator_id,
                action_type="delete_user",
                reason=reason,
                target_user_id=user_id
            )

            # Step 6: Delete auth user (CASCADE handles remaining data)
            self.supabase.auth.admin.delete_user(user_id)

            logger.info(f"Account deletion completed for user {user_id} by admin {moderator_id}")
            return {"user_id": user_id, "deleted": True}, None

        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return None, "An error occurred while deleting the user"
