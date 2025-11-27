"""
Repository layer for database operations
Repositories handle all database interactions using Supabase
"""

from app.repositories.base import BaseRepository
from app.repositories.recipe_repository import RecipeRepository
from app.repositories.user_saved_recipe_repository import UserSavedRecipeRepository
from app.repositories.video_creator_repository import VideoCreatorRepository
from app.repositories.video_source_repository import VideoSourceRepository
from app.repositories.collection_repository import CollectionRepository
from app.repositories.collection_recipe_repository import CollectionRecipeRepository

__all__ = [
    "BaseRepository",
    "RecipeRepository",
    "UserSavedRecipeRepository",
    "VideoCreatorRepository",
    "VideoSourceRepository",
    "CollectionRepository",
    "CollectionRecipeRepository",
]
