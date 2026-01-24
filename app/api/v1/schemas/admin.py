"""
Admin API schemas for moderation endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.domain.enums import ReportStatus


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class UpdateReportStatusRequest(BaseModel):
    """Request to update report status"""
    status: ReportStatus = Field(..., description="New status for the report")
    resolution_notes: Optional[str] = Field(None, max_length=2000)


class DismissReportRequest(BaseModel):
    """Request to dismiss a report"""
    reason: str = Field(..., max_length=500, description="Reason for dismissal")
    notes: Optional[str] = Field(None, max_length=2000)
    is_false_report: bool = Field(
        False,
        description="Mark as false/abusive report (affects reporter reliability)"
    )


class TakeActionRequest(BaseModel):
    """Request to take moderation action on a report"""
    action: str = Field(
        ...,
        description="Action to take: hide_recipe, warn_user, suspend_user, ban_user"
    )
    reason: str = Field(..., max_length=500, description="Reason for the action")
    notes: Optional[str] = Field(None, max_length=2000)
    suspension_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Days to suspend (required if action is suspend_user)"
    )


class ResolveFeedbackRequest(BaseModel):
    """Request to resolve extraction feedback"""
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    was_helpful: bool = Field(
        False,
        description="Whether the feedback was helpful for improvement"
    )


class HideRecipeRequest(BaseModel):
    """Request to hide a recipe"""
    reason: str = Field(..., max_length=500, description="Reason for hiding")


class UnhideRecipeRequest(BaseModel):
    """Request to unhide a recipe"""
    reason: str = Field(..., max_length=500, description="Reason for unhiding")


class WarnUserRequest(BaseModel):
    """Request to warn a user"""
    reason: str = Field(..., max_length=500, description="Reason for the warning")
    recipe_id: Optional[str] = Field(None, description="Related recipe ID")


class SuspendUserRequest(BaseModel):
    """Request to suspend a user"""
    duration_days: int = Field(
        ...,
        ge=1,
        le=365,
        description="Duration of suspension in days"
    )
    reason: str = Field(..., max_length=500, description="Reason for suspension")


class BanUserRequest(BaseModel):
    """Request to ban a user"""
    reason: str = Field(..., max_length=500, description="Reason for ban")


class UnsuspendUserRequest(BaseModel):
    """Request to remove suspension"""
    reason: str = Field(..., max_length=500, description="Reason for unsuspension")


class UnbanUserRequest(BaseModel):
    """Request to remove ban"""
    reason: str = Field(..., max_length=500, description="Reason for unban")


class SendNotificationRequest(BaseModel):
    """Request to send a push notification"""
    user_id: Optional[str] = Field(
        None,
        description="Target user ID. If None, broadcasts to all users with active tokens"
    )
    title: str = Field(..., min_length=1, max_length=100, description="Notification title")
    body: str = Field(..., min_length=1, max_length=500, description="Notification body")
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional payload data for deep linking"
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class SendNotificationResponse(BaseModel):
    """Response from sending a notification"""
    success: bool
    message: str
    sent_count: int = 0
    failed_count: int = 0


class UserSummaryAdmin(BaseModel):
    """User summary for admin views"""
    id: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class RecipeSummaryAdmin(BaseModel):
    """Recipe summary for admin views"""
    id: str
    title: str
    image_url: Optional[str] = None
    created_by: Optional[str] = None
    is_public: Optional[bool] = None
    source_url: Optional[str] = None


class RecipeDetailAdmin(BaseModel):
    """Full recipe details for admin review"""
    id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_by: Optional[str] = None
    is_public: Optional[bool] = None
    source_url: Optional[str] = None
    ingredients: Optional[List[Dict[str, Any]]] = None
    instructions: Optional[List[Dict[str, Any]]] = None


class ContentReportAdmin(BaseModel):
    """Content report for admin view"""
    id: str
    recipe_id: str
    reporter_user_id: str
    reason: str
    description: Optional[str] = None
    status: str
    priority: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

    # Nested objects
    recipes: Optional[RecipeSummaryAdmin] = None
    reporter: Optional[UserSummaryAdmin] = None
    resolved_by_user: Optional[UserSummaryAdmin] = None


class ContentReportDetailAdmin(BaseModel):
    """Full content report details for admin view"""
    id: str
    recipe_id: str
    reporter_user_id: str
    reason: str
    description: Optional[str] = None
    status: str
    priority: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

    # Full nested objects
    recipes: Optional[RecipeDetailAdmin] = None
    reporter: Optional[UserSummaryAdmin] = None
    resolved_by_user: Optional[UserSummaryAdmin] = None


class ExtractionFeedbackAdmin(BaseModel):
    """Extraction feedback for admin view"""
    id: str
    recipe_id: str
    user_id: str
    category: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    was_helpful: Optional[bool] = None

    # Nested objects
    recipes: Optional[RecipeSummaryAdmin] = None
    user: Optional[UserSummaryAdmin] = None


class UserModerationAdmin(BaseModel):
    """User moderation status for admin view"""
    id: str
    user_id: str
    status: str
    warning_count: int
    report_count: int
    false_report_count: int
    suspended_until: Optional[datetime] = None
    ban_reason: Optional[str] = None
    reporter_reliability_score: int
    created_at: datetime
    updated_at: datetime


class UserWarningAdmin(BaseModel):
    """User warning for admin view"""
    id: str
    user_id: str
    issued_by: str
    reason: str
    recipe_id: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    # Nested objects
    issuer: Optional[UserSummaryAdmin] = None
    recipes: Optional[RecipeSummaryAdmin] = None


class ModerationActionAdmin(BaseModel):
    """Moderation action for admin view"""
    id: str
    moderator_id: str
    action_type: str
    reason: str
    notes: Optional[str] = None
    duration_days: Optional[int] = None
    target_user_id: Optional[str] = None
    target_recipe_id: Optional[str] = None
    created_at: datetime

    # Nested objects
    moderator: Optional[UserSummaryAdmin] = None
    target_user: Optional[UserSummaryAdmin] = None
    target_recipe: Optional[RecipeSummaryAdmin] = None


class UserModerationDetailAdmin(BaseModel):
    """Complete user moderation details"""
    user: Optional[UserSummaryAdmin] = None
    moderation: UserModerationAdmin
    warnings: List[UserWarningAdmin]
    actions: List[ModerationActionAdmin]


class ReportQueueResponse(BaseModel):
    """Response for report queue"""
    reports: List[ContentReportAdmin]
    total: int


class FeedbackQueueResponse(BaseModel):
    """Response for feedback queue"""
    feedback: List[ExtractionFeedbackAdmin]
    total: int


class ReportStatistics(BaseModel):
    """Statistics for reports"""
    by_status: Dict[str, int]
    pending_by_reason: Dict[str, int]


class FeedbackStatistics(BaseModel):
    """Statistics for feedback"""
    by_status: Dict[str, int]
    pending_by_category: Dict[str, int]


class UserModerationStatistics(BaseModel):
    """Statistics for user moderation"""
    good_standing: int
    warned: int
    suspended: int
    banned: int


class ActionStatistics(BaseModel):
    """Statistics for moderation actions"""
    by_type: Dict[str, int]
    total: int
    period_days: int


class ModerationStatisticsResponse(BaseModel):
    """Combined moderation statistics"""
    reports: ReportStatistics
    feedback: FeedbackStatistics
    users: UserModerationStatistics
    actions: ActionStatistics


class AdminMeResponse(BaseModel):
    """Response for admin identity verification"""
    user_id: str
    email: Optional[str] = None
    is_admin: bool = True


# =============================================================================
# USER LIST SCHEMAS
# =============================================================================


class UserListItemAdmin(BaseModel):
    """User list item for admin view"""
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_sign_in_at: Optional[datetime] = None

    # Moderation status
    moderation_status: str = "good_standing"  # good_standing, warned, suspended, banned
    warning_count: int = 0
    report_count: int = 0  # reports AGAINST user

    # Reporter stats
    reports_submitted: int = 0  # reports BY user
    false_report_count: int = 0
    reporter_reliability_score: float = 1.0

    # Subscription info
    is_premium: bool = False
    subscription_expires_at: Optional[datetime] = None
    is_trial: bool = False


class UserListResponse(BaseModel):
    """Response for user list endpoint"""
    users: List[UserListItemAdmin]
    total: int


class UserFeedbackAdmin(BaseModel):
    """User's extraction feedback for admin view"""
    id: str
    recipe_id: str
    category: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    was_helpful: Optional[bool] = None

    # Nested objects
    recipes: Optional[RecipeSummaryAdmin] = None


class UserModerationDetailEnhancedAdmin(BaseModel):
    """Complete user details including feedback and subscription"""
    user: Optional[UserSummaryAdmin] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None
    moderation: UserModerationAdmin
    warnings: List[UserWarningAdmin]
    actions: List[ModerationActionAdmin]
    feedback: List[UserFeedbackAdmin] = []

    # Reporter stats
    reports_submitted: int = 0

    # Subscription info
    is_premium: bool = False
    subscription_product_id: Optional[str] = None
    subscription_expires_at: Optional[datetime] = None
    is_trial: bool = False


class DeleteUserRequest(BaseModel):
    """Request to delete a user"""
    reason: str = Field(..., max_length=500, description="Reason for deletion")


# =============================================================================
# HIDDEN RECIPES SCHEMAS
# =============================================================================


class HiddenRecipeAdmin(BaseModel):
    """Hidden recipe for admin view"""
    id: str
    title: str
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    hidden_at: Optional[datetime] = None
    hidden_reason: Optional[str] = None
    created_by: Optional[str] = None

    # Nested objects
    owner: Optional[UserSummaryAdmin] = None
    hidden_by: Optional[UserSummaryAdmin] = None


class HiddenRecipesResponse(BaseModel):
    """Response for hidden recipes list"""
    recipes: List[HiddenRecipeAdmin]
    total: int


# =============================================================================
# ADMIN RECIPES LIST SCHEMAS
# =============================================================================


class AdminRecipeListItem(BaseModel):
    """Recipe item for admin recipes list"""
    id: str
    title: str
    image_url: Optional[str] = None
    source_type: str
    source_url: Optional[str] = None
    is_public: bool = True
    is_draft: bool = False
    is_hidden: bool = False
    created_at: datetime
    created_by: str

    # Uploader info
    uploader: Optional[UserSummaryAdmin] = None


class AdminRecipesListResponse(BaseModel):
    """Response for admin recipes list endpoint"""
    recipes: List[AdminRecipeListItem]
    total: int


class AdminRecipeDetailResponse(BaseModel):
    """Full recipe details for admin view with moderation info"""
    id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    source_type: str
    source_url: Optional[str] = None
    is_public: bool = True
    is_draft: bool = False
    is_hidden: bool = False
    hidden_at: Optional[datetime] = None
    hidden_reason: Optional[str] = None
    created_at: datetime
    created_by: str

    # Recipe content
    ingredients: Optional[List[Dict[str, Any]]] = None
    instructions: Optional[List[Dict[str, Any]]] = None

    # Uploader info
    uploader: Optional[UserSummaryAdmin] = None

    # Who hid the recipe (if hidden)
    hidden_by: Optional[UserSummaryAdmin] = None
