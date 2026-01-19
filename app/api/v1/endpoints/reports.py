"""
Report endpoints for content reports and extraction feedback
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from supabase import Client
from typing import Optional
import logging

from app.core.database import get_supabase_client, get_supabase_user_client
from app.core.security import get_authenticated_user
from app.services.report_service import ReportService
from app.api.v1.schemas.report import (
    ContentReportRequest,
    ExtractionFeedbackRequest,
    ContentReportResponse,
    ExtractionFeedbackResponse,
    ReportReasonsResponse,
    FeedbackCategoriesResponse,
    UserReportsResponse,
    UserFeedbackResponse,
    ReportReasonOption,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


# =============================================================================
# CONTENT REPORTS
# =============================================================================


@router.post(
    "/content",
    response_model=ContentReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a content report",
    description="Report a recipe for policy violations such as inappropriate content, hate speech, copyright violation, etc."
)
async def submit_content_report(
    report_data: ContentReportRequest,
    request: Request,
    current_user: dict = Depends(get_authenticated_user),
):
    """Submit a content report for a recipe"""
    try:
        # Use user client for RLS-aware insert (auth.uid() must match reporter_user_id)
        supabase = get_supabase_user_client(request)
        service = ReportService(supabase)
        report, error = await service.submit_content_report(
            user_id=current_user["id"],
            recipe_id=report_data.recipe_id,
            reason=report_data.reason.value,
            description=report_data.description
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return ContentReportResponse(**report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting content report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit report"
        )


@router.get(
    "/content/my-reports",
    response_model=UserReportsResponse,
    summary="Get my content reports",
    description="Get content reports submitted by the current user"
)
async def get_my_content_reports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get content reports submitted by the current user"""
    try:
        service = ReportService(supabase)
        reports = await service.get_user_reports(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )

        return UserReportsResponse(
            reports=[ContentReportResponse(**r) for r in reports],
            total=len(reports)
        )

    except Exception as e:
        logger.error(f"Error fetching user reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reports"
        )


@router.get(
    "/content/reasons",
    response_model=ReportReasonsResponse,
    summary="Get report reasons",
    description="Get available reasons for content reports with descriptions"
)
async def get_report_reasons(
    supabase: Client = Depends(get_supabase_client)
):
    """Get available report reasons"""
    try:
        service = ReportService(supabase)
        reasons = await service.get_report_reasons()

        return ReportReasonsResponse(
            reasons=[ReportReasonOption(**r) for r in reasons]
        )

    except Exception as e:
        logger.error(f"Error fetching report reasons: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch report reasons"
        )


# =============================================================================
# EXTRACTION FEEDBACK
# =============================================================================


@router.post(
    "/extraction-feedback",
    response_model=ExtractionFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit extraction feedback",
    description="Submit feedback about AI extraction quality issues such as wrong ingredients, missing steps, etc."
)
async def submit_extraction_feedback(
    feedback_data: ExtractionFeedbackRequest,
    request: Request,
    current_user: dict = Depends(get_authenticated_user),
):
    """Submit extraction feedback for a recipe"""
    try:
        # Use user client for RLS-aware insert (auth.uid() must match user_id)
        supabase = get_supabase_user_client(request)
        service = ReportService(supabase)
        feedback, error = await service.submit_extraction_feedback(
            user_id=current_user["id"],
            recipe_id=feedback_data.recipe_id,
            category=feedback_data.category.value,
            description=feedback_data.description,
            extraction_job_id=feedback_data.extraction_job_id
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return ExtractionFeedbackResponse(**feedback)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting extraction feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get(
    "/extraction-feedback/my-feedback",
    response_model=UserFeedbackResponse,
    summary="Get my extraction feedback",
    description="Get extraction feedback submitted by the current user"
)
async def get_my_extraction_feedback(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_authenticated_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get extraction feedback submitted by the current user"""
    try:
        service = ReportService(supabase)
        feedback = await service.get_user_feedback(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )

        return UserFeedbackResponse(
            feedback=[ExtractionFeedbackResponse(**f) for f in feedback],
            total=len(feedback)
        )

    except Exception as e:
        logger.error(f"Error fetching user feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback"
        )


@router.get(
    "/extraction-feedback/categories",
    response_model=FeedbackCategoriesResponse,
    summary="Get feedback categories",
    description="Get available categories for extraction feedback with descriptions"
)
async def get_feedback_categories(
    supabase: Client = Depends(get_supabase_client)
):
    """Get available feedback categories"""
    try:
        service = ReportService(supabase)
        categories = await service.get_feedback_categories()

        return FeedbackCategoriesResponse(
            categories=[ReportReasonOption(**c) for c in categories]
        )

    except Exception as e:
        logger.error(f"Error fetching feedback categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback categories"
        )
