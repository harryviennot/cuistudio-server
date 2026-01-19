"""
Admin endpoints for content moderation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client
from typing import Optional
import logging

from app.core.database import get_supabase_admin_client
from app.core.security import get_admin_user
from app.services.moderation_service import ModerationService
from app.api.v1.schemas.admin import (
    # Request schemas
    DismissReportRequest,
    TakeActionRequest,
    ResolveFeedbackRequest,
    HideRecipeRequest,
    UnhideRecipeRequest,
    WarnUserRequest,
    SuspendUserRequest,
    BanUserRequest,
    UnsuspendUserRequest,
    UnbanUserRequest,
    DeleteUserRequest,
    # Response schemas
    AdminMeResponse,
    ContentReportAdmin,
    ContentReportDetailAdmin,
    ExtractionFeedbackAdmin,
    ReportQueueResponse,
    FeedbackQueueResponse,
    UserModerationDetailEnhancedAdmin,
    UserListItemAdmin,
    UserListResponse,
    ModerationStatisticsResponse,
    HiddenRecipeAdmin,
    HiddenRecipesResponse,
)
from app.api.v1.schemas.common import MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


# =============================================================================
# ADMIN IDENTITY
# =============================================================================


@router.get(
    "/me",
    response_model=AdminMeResponse,
    summary="Verify admin identity",
    description="Verify the current user is an admin and return their info"
)
async def get_admin_me(
    current_user: dict = Depends(get_admin_user),
):
    """
    Verify current user is admin.
    Returns 403 if not admin (handled by get_admin_user dependency).
    """
    return AdminMeResponse(
        user_id=current_user["id"],
        email=current_user.get("email"),
        is_admin=True
    )


# =============================================================================
# USER LIST & MANAGEMENT
# =============================================================================


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="Get user list",
    description="Get paginated list of users with moderation and subscription info"
)
async def get_users(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by moderation status"),
    is_premium: Optional[bool] = Query(None, description="Filter by premium status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    sort_by: str = Query("created_at", description="Sort field: created_at, name, last_sign_in_at"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Get paginated user list with moderation and subscription info"""
    try:
        service = ModerationService(supabase)
        result = await service.get_users_list(
            status=status_filter,
            is_premium=is_premium,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

        return UserListResponse(
            users=[UserListItemAdmin(**u) for u in result["users"]],
            total=result["total"]
        )

    except Exception as e:
        logger.error(f"Error fetching user list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


# =============================================================================
# CONTENT REPORT MANAGEMENT
# =============================================================================


@router.get(
    "/reports",
    response_model=ReportQueueResponse,
    summary="Get report queue",
    description="Get pending content reports for review, sorted by priority"
)
async def get_report_queue(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    reason: Optional[str] = Query(None, description="Filter by reason"),
    min_priority: Optional[int] = Query(None, description="Minimum priority"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Get pending content reports"""
    try:
        service = ModerationService(supabase)
        reports = await service.get_report_queue(
            status=status_filter,
            reason=reason,
            min_priority=min_priority,
            limit=limit,
            offset=offset
        )

        return ReportQueueResponse(
            reports=[ContentReportAdmin(**r) for r in reports],
            total=len(reports)
        )

    except Exception as e:
        logger.error(f"Error fetching report queue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reports"
        )


@router.get(
    "/reports/{report_id}",
    response_model=ContentReportDetailAdmin,
    summary="Get report details",
    description="Get full details of a content report including recipe content"
)
async def get_report_details(
    report_id: str,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Get full details of a content report"""
    try:
        service = ModerationService(supabase)
        report = await service.get_report_details(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )

        return ContentReportDetailAdmin(**report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching report details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch report details"
        )


@router.post(
    "/reports/{report_id}/dismiss",
    response_model=ContentReportAdmin,
    summary="Dismiss report",
    description="Dismiss a content report as invalid or already addressed"
)
async def dismiss_report(
    report_id: str,
    request: DismissReportRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Dismiss a content report"""
    try:
        service = ModerationService(supabase)
        report, error = await service.dismiss_report(
            moderator_id=current_user["id"],
            report_id=report_id,
            reason=request.reason,
            notes=request.notes,
            is_false_report=request.is_false_report
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return ContentReportAdmin(**report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to dismiss report"
        )


@router.post(
    "/reports/{report_id}/action",
    response_model=MessageResponse,
    summary="Take action on report",
    description="Take moderation action based on a content report"
)
async def take_action_on_report(
    report_id: str,
    request: TakeActionRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Take moderation action on a report"""
    try:
        service = ModerationService(supabase)
        result, error = await service.take_action_on_report(
            moderator_id=current_user["id"],
            report_id=report_id,
            action=request.action,
            reason=request.reason,
            notes=request.notes,
            suspension_days=request.suspension_days
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message=f"Action '{request.action}' taken successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error taking action on report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to take action"
        )


# =============================================================================
# EXTRACTION FEEDBACK MANAGEMENT
# =============================================================================


@router.get(
    "/extraction-feedback",
    response_model=FeedbackQueueResponse,
    summary="Get feedback queue",
    description="Get pending extraction feedback for review"
)
async def get_feedback_queue(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Get pending extraction feedback"""
    try:
        service = ModerationService(supabase)
        feedback = await service.get_feedback_queue(
            status=status_filter,
            category=category,
            limit=limit,
            offset=offset
        )

        return FeedbackQueueResponse(
            feedback=[ExtractionFeedbackAdmin(**f) for f in feedback],
            total=len(feedback)
        )

    except Exception as e:
        logger.error(f"Error fetching feedback queue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback"
        )


@router.get(
    "/extraction-feedback/{feedback_id}",
    response_model=ExtractionFeedbackAdmin,
    summary="Get feedback details",
    description="Get full details of extraction feedback"
)
async def get_feedback_details(
    feedback_id: str,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Get full details of extraction feedback"""
    try:
        service = ModerationService(supabase)
        feedback = await service.get_feedback_details(feedback_id)

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )

        return ExtractionFeedbackAdmin(**feedback)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching feedback details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback details"
        )


@router.post(
    "/extraction-feedback/{feedback_id}/resolve",
    response_model=ExtractionFeedbackAdmin,
    summary="Resolve feedback",
    description="Mark extraction feedback as resolved"
)
async def resolve_feedback(
    feedback_id: str,
    request: ResolveFeedbackRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Resolve extraction feedback"""
    try:
        service = ModerationService(supabase)
        feedback, error = await service.resolve_feedback(
            moderator_id=current_user["id"],
            feedback_id=feedback_id,
            resolution_notes=request.resolution_notes,
            was_helpful=request.was_helpful
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return ExtractionFeedbackAdmin(**feedback)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve feedback"
        )


# =============================================================================
# RECIPE MODERATION
# =============================================================================


@router.get(
    "/recipes/hidden",
    response_model=HiddenRecipesResponse,
    summary="Get hidden recipes",
    description="Get paginated list of hidden recipes with moderation details"
)
async def get_hidden_recipes(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Get list of all hidden recipes with owner and moderator info"""
    try:
        service = ModerationService(supabase)
        result = await service.get_hidden_recipes(
            limit=limit,
            offset=offset
        )

        return HiddenRecipesResponse(
            recipes=[HiddenRecipeAdmin(**r) for r in result["recipes"]],
            total=result["total"]
        )

    except Exception as e:
        logger.error(f"Error fetching hidden recipes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch hidden recipes"
        )


@router.post(
    "/recipes/{recipe_id}/hide",
    response_model=MessageResponse,
    summary="Hide recipe",
    description="Hide a recipe from public view"
)
async def hide_recipe(
    recipe_id: str,
    request: HideRecipeRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Hide a recipe from public view"""
    try:
        service = ModerationService(supabase)
        result, error = await service.hide_recipe(
            moderator_id=current_user["id"],
            recipe_id=recipe_id,
            reason=request.reason
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message="Recipe hidden successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error hiding recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to hide recipe"
        )


@router.post(
    "/recipes/{recipe_id}/unhide",
    response_model=MessageResponse,
    summary="Unhide recipe",
    description="Restore a hidden recipe to public view"
)
async def unhide_recipe(
    recipe_id: str,
    request: UnhideRecipeRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Restore a hidden recipe"""
    try:
        service = ModerationService(supabase)
        result, error = await service.unhide_recipe(
            moderator_id=current_user["id"],
            recipe_id=recipe_id,
            reason=request.reason
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message="Recipe unhidden successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unhiding recipe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unhide recipe"
        )


# =============================================================================
# USER MODERATION
# =============================================================================


@router.get(
    "/users/{user_id}",
    response_model=UserModerationDetailEnhancedAdmin,
    summary="Get user moderation details",
    description="Get complete moderation details for a user including feedback and subscription"
)
async def get_user_moderation_details(
    user_id: str,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Get enhanced user moderation details including feedback and subscription"""
    try:
        service = ModerationService(supabase)
        details = await service.get_user_moderation_details_enhanced(user_id)

        return UserModerationDetailEnhancedAdmin(**details)

    except Exception as e:
        logger.error(f"Error fetching user moderation details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user details"
        )


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Delete user",
    description="Permanently delete a user account"
)
async def delete_user(
    user_id: str,
    request: DeleteUserRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Delete a user account. Transfers video recipes to system account, deletes personal recipes."""
    try:
        service = ModerationService(supabase)
        result, error = await service.delete_user(
            moderator_id=current_user["id"],
            user_id=user_id,
            reason=request.reason
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message="User deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@router.post(
    "/users/{user_id}/warn",
    response_model=MessageResponse,
    summary="Warn user",
    description="Issue a warning to a user"
)
async def warn_user(
    user_id: str,
    request: WarnUserRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Issue a warning to a user"""
    try:
        service = ModerationService(supabase)
        result, error = await service.warn_user(
            moderator_id=current_user["id"],
            user_id=user_id,
            reason=request.reason,
            recipe_id=request.recipe_id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message="Warning issued successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error warning user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to issue warning"
        )


@router.post(
    "/users/{user_id}/suspend",
    response_model=MessageResponse,
    summary="Suspend user",
    description="Temporarily suspend a user"
)
async def suspend_user(
    user_id: str,
    request: SuspendUserRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Suspend a user temporarily"""
    try:
        service = ModerationService(supabase)
        result, error = await service.suspend_user(
            moderator_id=current_user["id"],
            user_id=user_id,
            duration_days=request.duration_days,
            reason=request.reason
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message=f"User suspended for {request.duration_days} days")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suspending user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend user"
        )


@router.post(
    "/users/{user_id}/unsuspend",
    response_model=MessageResponse,
    summary="Unsuspend user",
    description="Remove suspension from a user"
)
async def unsuspend_user(
    user_id: str,
    request: UnsuspendUserRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Remove suspension from a user"""
    try:
        service = ModerationService(supabase)
        result, error = await service.unsuspend_user(
            moderator_id=current_user["id"],
            user_id=user_id,
            reason=request.reason
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message="User unsuspended successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsuspending user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsuspend user"
        )


@router.post(
    "/users/{user_id}/ban",
    response_model=MessageResponse,
    summary="Ban user",
    description="Permanently ban a user"
)
async def ban_user(
    user_id: str,
    request: BanUserRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Permanently ban a user"""
    try:
        service = ModerationService(supabase)
        result, error = await service.ban_user(
            moderator_id=current_user["id"],
            user_id=user_id,
            reason=request.reason
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message="User banned successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error banning user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ban user"
        )


@router.post(
    "/users/{user_id}/unban",
    response_model=MessageResponse,
    summary="Unban user",
    description="Remove ban from a user"
)
async def unban_user(
    user_id: str,
    request: UnbanUserRequest,
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Remove ban from a user"""
    try:
        service = ModerationService(supabase)
        result, error = await service.unban_user(
            moderator_id=current_user["id"],
            user_id=user_id,
            reason=request.reason
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return MessageResponse(message="User unbanned successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unbanning user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unban user"
        )


# =============================================================================
# STATISTICS
# =============================================================================


@router.get(
    "/statistics",
    response_model=ModerationStatisticsResponse,
    summary="Get moderation statistics",
    description="Get overall moderation statistics"
)
async def get_moderation_statistics(
    current_user: dict = Depends(get_admin_user),
    supabase: Client = Depends(get_supabase_admin_client)
):
    """Get moderation statistics"""
    try:
        service = ModerationService(supabase)
        stats = await service.get_statistics()

        return ModerationStatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Error fetching moderation statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )
