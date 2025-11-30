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
