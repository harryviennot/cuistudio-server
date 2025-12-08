"""
Discovery-related schemas for recipe discovery endpoints.
"""
from enum import Enum
from pydantic import BaseModel

from app.api.v1.schemas.recipe import RecipeResponse, UserRecipeDataResponse


class SourceCategory(str, Enum):
    """Source category for filtering extracted recipes"""
    VIDEO = "video"  # TikTok, Instagram, YouTube
    WEBSITE = "website"  # Recipe websites/URLs


class ExtractionStatsResponse(BaseModel):
    """Extraction statistics for a recipe"""
    extraction_count: int
    unique_extractors: int


class MostExtractedRecipeResponse(RecipeResponse):
    """Recipe with extraction statistics"""
    extraction_stats: ExtractionStatsResponse


class HighestRatedRecipeResponse(RecipeResponse):
    """Recipe response for highest rated endpoint.

    Uses the existing average_rating and rating_count fields
    from RecipeResponse - no additional fields needed.
    """
    pass


class RecentRecipeResponse(RecipeResponse):
    """Recipe response for recently added endpoint.

    Uses the existing created_at field from RecipeResponse.
    """
    pass


# Rebuild models to resolve forward references from RecipeResponse
# RecipeResponse has Optional['UserRecipeDataResponse'] which needs resolution
MostExtractedRecipeResponse.model_rebuild()
HighestRatedRecipeResponse.model_rebuild()
RecentRecipeResponse.model_rebuild()
