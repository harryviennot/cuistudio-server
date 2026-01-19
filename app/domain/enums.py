"""
Enumerations for domain models
"""
from enum import Enum


class SourceType(str, Enum):
    """Recipe source types"""
    VIDEO = "video"  # Deprecated - use LINK instead
    PHOTO = "photo"
    VOICE = "voice"
    PASTE = "paste"
    LINK = "link"  # Auto-detects video vs webpage


class DifficultyLevel(str, Enum):
    """Recipe difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ExtractionStatus(str, Enum):
    """Recipe extraction job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NOT_A_RECIPE = "not_a_recipe"  # Content doesn't contain a recipe
    WEBSITE_BLOCKED = "website_blocked"  # Website blocks automated extraction
    NEEDS_CLIENT_DOWNLOAD = "needs_client_download"  # Client needs to download video (Instagram)


class PermissionLevel(str, Enum):
    """Sharing permission levels"""
    VIEW = "view"
    FORK = "fork"
    COLLABORATE = "collaborate"  # Can edit


class ContributionType(str, Enum):
    """Type of contribution to a recipe"""
    CREATOR = "creator"
    FORK = "fork"
    EDIT = "edit"


class FeaturedType(str, Enum):
    """Featured recipe types"""
    MANUAL = "manual"  # Manually curated
    TRENDING = "trending"
    POPULAR = "popular"
    TIME_OF_DAY = "time_of_day"  # Breakfast, lunch, dinner based on time


class RecipeMode(str, Enum):
    """Recipe viewing modes"""
    VIEW = "view"
    EDIT = "edit"
    FORK = "fork"
    COOK = "cook"


class SubscriptionStatus(str, Enum):
    """User subscription status"""
    NONE = "none"
    ACTIVE = "active"
    TRIALING = "trialing"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    BILLING_ISSUE = "billing_issue"


class CreditType(str, Enum):
    """Types of credits"""
    STANDARD = "standard"
    REFERRAL = "referral"


class CreditTransactionReason(str, Enum):
    """Reasons for credit changes"""
    EXTRACTION = "extraction"
    WEEKLY_RESET = "weekly_reset"
    REFERRAL_BONUS = "referral_bonus"
    EXPIRED = "expired"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class ReferralSource(str, Enum):
    """Source of referral credits"""
    REFERRER = "referrer"
    REFEREE = "referee"


# =============================================================================
# MODERATION ENUMS
# =============================================================================


class ContentReportReason(str, Enum):
    """Reasons for reporting recipe content"""
    INAPPROPRIATE_CONTENT = "inappropriate_content"  # Explicit, violent, or otherwise inappropriate
    HATE_SPEECH = "hate_speech"  # Hate speech or discrimination
    COPYRIGHT_VIOLATION = "copyright_violation"  # Copyrighted content without permission
    SPAM_ADVERTISING = "spam_advertising"  # Spam or advertising
    MISINFORMATION = "misinformation"  # Dangerous cooking advice (food safety)
    OTHER = "other"  # Other (requires description)


class ExtractionFeedbackCategory(str, Enum):
    """Categories for extraction quality feedback"""
    WRONG_INGREDIENTS = "wrong_ingredients"  # Ingredients don't match source
    MISSING_STEPS = "missing_steps"  # Instructions missing steps
    INCORRECT_STEPS = "incorrect_steps"  # Instructions are wrong
    BAD_FORMATTING = "bad_formatting"  # Formatting issues, unclear text
    WRONG_MEASUREMENTS = "wrong_measurements"  # Quantities wrong
    WRONG_SERVINGS = "wrong_servings"  # Serving count incorrect
    AI_HALLUCINATION = "ai_hallucination"  # AI added content not in source
    WRONG_TITLE = "wrong_title"  # Title doesn't match recipe
    WRONG_IMAGE = "wrong_image"  # Image doesn't match recipe
    OTHER = "other"  # Other (requires description)


class ReportStatus(str, Enum):
    """Status of a report or feedback"""
    PENDING = "pending"  # Awaiting review
    IN_REVIEW = "in_review"  # Being reviewed by moderator
    RESOLVED = "resolved"  # Resolved (action taken or dismissed)
    ESCALATED = "escalated"  # Escalated for further review


class UserModerationStatus(str, Enum):
    """User moderation status"""
    GOOD_STANDING = "good_standing"  # Normal user
    WARNED = "warned"  # Has received warnings
    SUSPENDED = "suspended"  # Temporarily suspended
    BANNED = "banned"  # Permanently banned


class ModerationActionType(str, Enum):
    """Types of moderation actions"""
    DISMISS_REPORT = "dismiss_report"  # No action needed
    HIDE_RECIPE = "hide_recipe"  # Remove from public view
    UNHIDE_RECIPE = "unhide_recipe"  # Restore to public view
    WARN_USER = "warn_user"  # Issue warning to user
    SUSPEND_USER = "suspend_user"  # Temporary suspension
    UNSUSPEND_USER = "unsuspend_user"  # Remove suspension
    BAN_USER = "ban_user"  # Permanent ban
    UNBAN_USER = "unban_user"  # Remove ban
    RESOLVE_FEEDBACK = "resolve_feedback"  # Mark extraction feedback as resolved
