"""
Report service for handling content reports and extraction feedback.

Business Rules:
- Users can report recipes for policy violations
- Users can submit extraction quality feedback
- Rate limit: 10 reports per 24 hours per user
- Duplicate reports (same user, same recipe) are prevented
- Banned/suspended users cannot submit reports
- Low reliability users have restricted reporting
"""
from typing import Optional, List, Dict, Any, Tuple
from supabase import Client
import logging

from app.domain.enums import (
    ContentReportReason,
    ExtractionFeedbackCategory,
)
from app.repositories.content_report_repository import ContentReportRepository
from app.repositories.extraction_feedback_repository import ExtractionFeedbackRepository
from app.repositories.user_moderation_repository import UserModerationRepository

logger = logging.getLogger(__name__)

# Constants
MAX_REPORTS_PER_DAY = 10
MIN_RELIABILITY_TO_REPORT = 20


class ReportService:
    """Service for handling content reports and extraction feedback"""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.content_report_repo = ContentReportRepository(supabase)
        self.extraction_feedback_repo = ExtractionFeedbackRepository(supabase)
        self.user_moderation_repo = UserModerationRepository(supabase)

    async def submit_content_report(
        self,
        user_id: str,
        recipe_id: str,
        reason: str,
        description: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Submit a content report for a recipe.

        Args:
            user_id: ID of the reporting user
            recipe_id: ID of the recipe being reported
            reason: Report reason (from ContentReportReason enum)
            description: Optional additional details

        Returns:
            Tuple of (created report, error message if any)
        """
        try:
            # Validate reason
            if reason not in [r.value for r in ContentReportReason]:
                return None, f"Invalid report reason: {reason}"

            # Check if user can report
            can_report, error = await self._can_user_report(user_id)
            if not can_report:
                return None, error

            # Check for duplicate report
            existing = await self.content_report_repo.check_existing_report(
                recipe_id, user_id
            )
            if existing:
                return None, "You have already reported this recipe"

            # Check rate limit
            recent_count = await self.content_report_repo.count_user_recent_reports(
                user_id, hours=24
            )
            if recent_count >= MAX_REPORTS_PER_DAY:
                return None, f"Report limit reached. You can submit up to {MAX_REPORTS_PER_DAY} reports per day."

            # Get recipe info to increment report count for owner
            recipe_response = self.supabase.table("recipes")\
                .select("created_by")\
                .eq("id", recipe_id)\
                .single()\
                .execute()

            if not recipe_response.data:
                return None, "Recipe not found"

            recipe_owner_id = recipe_response.data.get("created_by")

            # Create the report
            report = await self.content_report_repo.create_report(
                recipe_id=recipe_id,
                reporter_user_id=user_id,
                reason=reason,
                description=description
            )

            if not report:
                return None, "Failed to create report"

            # Increment report count for recipe owner
            if recipe_owner_id:
                await self.user_moderation_repo.increment_report_count(recipe_owner_id)

            logger.info(f"Content report created: {report['id']} by user {user_id} for recipe {recipe_id}")
            return report, None

        except Exception as e:
            logger.error(f"Error submitting content report: {str(e)}")
            return None, "An error occurred while submitting the report"

    async def submit_extraction_feedback(
        self,
        user_id: str,
        recipe_id: str,
        category: str,
        description: Optional[str] = None,
        extraction_job_id: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Submit extraction quality feedback for a recipe.

        Args:
            user_id: ID of the user submitting feedback
            recipe_id: ID of the recipe with extraction issues
            category: Feedback category (from ExtractionFeedbackCategory enum)
            description: Optional additional details
            extraction_job_id: Optional link to extraction job

        Returns:
            Tuple of (created feedback, error message if any)
        """
        try:
            # Validate category
            if category not in [c.value for c in ExtractionFeedbackCategory]:
                return None, f"Invalid feedback category: {category}"

            # Check if user can report (same rules apply)
            can_report, error = await self._can_user_report(user_id)
            if not can_report:
                return None, error

            # Check for duplicate feedback (same category)
            existing = await self.extraction_feedback_repo.check_existing_feedback(
                recipe_id, user_id, category
            )
            if existing:
                return None, "You have already submitted feedback for this category on this recipe"

            # Create the feedback
            feedback = await self.extraction_feedback_repo.create_feedback(
                recipe_id=recipe_id,
                user_id=user_id,
                category=category,
                description=description,
                extraction_job_id=extraction_job_id
            )

            if not feedback:
                return None, "Failed to submit feedback"

            logger.info(f"Extraction feedback created: {feedback['id']} by user {user_id} for recipe {recipe_id}")
            return feedback, None

        except Exception as e:
            logger.error(f"Error submitting extraction feedback: {str(e)}")
            return None, "An error occurred while submitting feedback"

    async def get_user_reports(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get content reports submitted by a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of reports to return
            offset: Number of reports to skip

        Returns:
            List of content reports with recipe info
        """
        return await self.content_report_repo.get_user_reports(user_id, limit, offset)

    async def get_user_feedback(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get extraction feedback submitted by a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of feedback items to return
            offset: Number of items to skip

        Returns:
            List of extraction feedback with recipe info
        """
        return await self.extraction_feedback_repo.get_user_feedback(user_id, limit, offset)

    async def _can_user_report(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a user can submit reports.

        Args:
            user_id: ID of the user

        Returns:
            Tuple of (can_report, error_message)
        """
        try:
            # Check if user is banned
            is_banned = await self.user_moderation_repo.is_user_banned(user_id)
            if is_banned:
                return False, "Your account has been banned and cannot submit reports"

            # Check if user is suspended
            is_suspended = await self.user_moderation_repo.is_user_suspended(user_id)
            if is_suspended:
                return False, "Your account is temporarily suspended and cannot submit reports"

            # Check reporter reliability
            can_report = await self.user_moderation_repo.can_user_report(user_id)
            if not can_report:
                return False, "Your reporting privileges have been restricted due to false reports"

            return True, None

        except Exception as e:
            logger.error(f"Error checking user report ability: {str(e)}")
            # Allow reporting by default if check fails
            return True, None

    async def get_report_reasons(self) -> List[Dict[str, str]]:
        """
        Get available report reasons with descriptions.

        Returns:
            List of report reasons with value and label
        """
        return [
            {
                "value": ContentReportReason.INAPPROPRIATE_CONTENT.value,
                "label": "Inappropriate Content",
                "description": "Contains explicit, violent, or otherwise inappropriate material"
            },
            {
                "value": ContentReportReason.HATE_SPEECH.value,
                "label": "Hate Speech",
                "description": "Contains hate speech or discrimination"
            },
            {
                "value": ContentReportReason.COPYRIGHT_VIOLATION.value,
                "label": "Copyright Violation",
                "description": "Uses copyrighted content without permission"
            },
            {
                "value": ContentReportReason.SPAM_ADVERTISING.value,
                "label": "Spam / Advertising",
                "description": "Contains spam or advertising"
            },
            {
                "value": ContentReportReason.MISINFORMATION.value,
                "label": "Dangerous Misinformation",
                "description": "Contains dangerous cooking advice or food safety misinformation"
            },
            {
                "value": ContentReportReason.OTHER.value,
                "label": "Other",
                "description": "Other issue not listed above"
            },
        ]

    async def get_feedback_categories(self) -> List[Dict[str, str]]:
        """
        Get available extraction feedback categories with descriptions.

        Returns:
            List of feedback categories with value and label
        """
        return [
            {
                "value": ExtractionFeedbackCategory.WRONG_INGREDIENTS.value,
                "label": "Wrong Ingredients",
                "description": "The ingredients don't match the original source"
            },
            {
                "value": ExtractionFeedbackCategory.MISSING_STEPS.value,
                "label": "Missing Steps",
                "description": "Some instructions are missing"
            },
            {
                "value": ExtractionFeedbackCategory.INCORRECT_STEPS.value,
                "label": "Incorrect Steps",
                "description": "The instructions are wrong or in wrong order"
            },
            {
                "value": ExtractionFeedbackCategory.BAD_FORMATTING.value,
                "label": "Bad Formatting",
                "description": "Text is poorly formatted or hard to read"
            },
            {
                "value": ExtractionFeedbackCategory.WRONG_MEASUREMENTS.value,
                "label": "Wrong Measurements",
                "description": "Quantities or measurements are incorrect"
            },
            {
                "value": ExtractionFeedbackCategory.WRONG_SERVINGS.value,
                "label": "Wrong Servings",
                "description": "Serving count is incorrect"
            },
            {
                "value": ExtractionFeedbackCategory.AI_HALLUCINATION.value,
                "label": "AI Added Fake Content",
                "description": "AI added content that wasn't in the original source"
            },
            {
                "value": ExtractionFeedbackCategory.WRONG_TITLE.value,
                "label": "Wrong Title",
                "description": "The recipe title doesn't match the content"
            },
            {
                "value": ExtractionFeedbackCategory.WRONG_IMAGE.value,
                "label": "Wrong Image",
                "description": "The image doesn't match the recipe"
            },
            {
                "value": ExtractionFeedbackCategory.OTHER.value,
                "label": "Other",
                "description": "Other extraction issue not listed above"
            },
        ]
