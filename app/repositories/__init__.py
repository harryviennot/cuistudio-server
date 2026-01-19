"""
Repository layer for database operations
Repositories handle all database interactions using Supabase
"""

from app.repositories.base import BaseRepository
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.user_saved_recipe_repository import UserSavedRecipeRepository
from app.repositories.user_recipe_repository import UserRecipeRepository
from app.repositories.video_creator_repository import VideoCreatorRepository
from app.repositories.video_source_repository import VideoSourceRepository
from app.repositories.content_report_repository import ContentReportRepository
from app.repositories.extraction_feedback_repository import ExtractionFeedbackRepository
from app.repositories.user_moderation_repository import UserModerationRepository
from app.repositories.moderation_action_repository import (
    ModerationActionRepository,
    UserWarningRepository,
)

__all__ = [
    "BaseRepository",
    "RecipeRepository",
    "UserSavedRecipeRepository",
    "UserRecipeRepository",
    "VideoCreatorRepository",
    "VideoSourceRepository",
    "ContentReportRepository",
    "ExtractionFeedbackRepository",
    "UserModerationRepository",
    "ModerationActionRepository",
    "UserWarningRepository",
]
