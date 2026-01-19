"""
Report API schemas for content reports and extraction feedback
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.domain.enums import (
    ContentReportReason,
    ExtractionFeedbackCategory,
)


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class ContentReportRequest(BaseModel):
    """Request to submit a content report"""
    recipe_id: str = Field(..., description="ID of the recipe being reported")
    reason: ContentReportReason = Field(..., description="Reason for the report")
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional additional details about the report"
    )


class ExtractionFeedbackRequest(BaseModel):
    """Request to submit extraction feedback"""
    recipe_id: str = Field(..., description="ID of the recipe with extraction issues")
    category: ExtractionFeedbackCategory = Field(..., description="Category of the issue")
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional additional details about the issue"
    )
    extraction_job_id: Optional[str] = Field(
        None,
        description="Optional extraction job ID for debugging"
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class RecipeSummary(BaseModel):
    """Summary of a recipe for reports"""
    id: str
    title: str
    image_url: Optional[str] = None


class UserSummary(BaseModel):
    """Summary of a user for reports"""
    id: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class ContentReportResponse(BaseModel):
    """Response for a content report"""
    id: str
    recipe_id: str
    reason: str
    description: Optional[str] = None
    status: str
    priority: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Nested objects (optional, populated when fetching with details)
    recipes: Optional[RecipeSummary] = None


class ExtractionFeedbackResponse(BaseModel):
    """Response for extraction feedback"""
    id: str
    recipe_id: str
    category: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    was_helpful: Optional[bool] = None

    # Nested objects (optional)
    recipes: Optional[RecipeSummary] = None


class ReportReasonOption(BaseModel):
    """A report reason option with description"""
    value: str
    label: str
    description: str


class ReportReasonsResponse(BaseModel):
    """Available report reasons"""
    reasons: List[ReportReasonOption]


class FeedbackCategoriesResponse(BaseModel):
    """Available feedback categories"""
    categories: List[ReportReasonOption]


class UserReportsResponse(BaseModel):
    """Response for user's submitted reports"""
    reports: List[ContentReportResponse]
    total: int


class UserFeedbackResponse(BaseModel):
    """Response for user's submitted feedback"""
    feedback: List[ExtractionFeedbackResponse]
    total: int
