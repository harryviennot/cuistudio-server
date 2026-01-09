"""
User recipe data repository
"""
from typing import Optional, Dict, Any, List
from supabase import Client
import logging
from datetime import datetime, timezone

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class UserRecipeRepository(BaseRepository):
    """Repository for user-specific recipe data"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "user_recipe_data")

    async def get_by_user_and_recipe(
        self,
        user_id: str,
        recipe_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user data for a specific recipe"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("recipe_id", recipe_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching user recipe data: {str(e)}")
            raise

    async def get_user_data_for_recipes(
        self,
        user_id: str,
        recipe_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Batch fetch user data for multiple recipes in a single query.
        Returns a dict mapping recipe_id -> user_data

        This eliminates N+1 query problem when loading recipe lists.
        """
        try:
            if not recipe_ids:
                return {}

            response = self.supabase.table(self.table_name)\
                .select("recipe_id, rating, is_favorite, times_cooked, last_cooked_at, custom_prep_time_minutes, custom_cook_time_minutes, custom_difficulty, notes, custom_servings")\
                .eq("user_id", user_id)\
                .in_("recipe_id", recipe_ids)\
                .execute()

            # Create map of recipe_id -> user_data for O(1) lookups
            return {row["recipe_id"]: row for row in (response.data or [])}
        except Exception as e:
            logger.error(f"Error batch fetching user recipe data: {str(e)}")
            raise

    async def upsert_user_data(
        self,
        user_id: str,
        recipe_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create or update user recipe data"""
        try:
            # Add user_id and recipe_id to data
            full_data = {
                "user_id": user_id,
                "recipe_id": recipe_id,
                **data
            }

            response = self.supabase.table(self.table_name)\
                .upsert(full_data, on_conflict="user_id,recipe_id")\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error upserting user recipe data: {str(e)}")
            raise

    async def get_user_favorites(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> list[Dict[str, Any]]:
        """Get user's favorite recipes"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, recipes(*)")\
                .eq("user_id", user_id)\
                .eq("is_favorite", True)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user favorites: {str(e)}")
            raise

    async def increment_cooked_count(
        self,
        user_id: str,
        recipe_id: str,
        rating: Optional[float] = None,
        image_url: Optional[str] = None,
        duration_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Increment the times cooked counter and record cooking event with session data.

        This performs multiple operations:
        1. Inserts a cooking event with optional rating, photo, and duration
        2. Updates user_recipe_data.times_cooked (personal count)
        3. Updates user_recipe_data.rating if rating is provided
        4. Updates user_recipe_data.last_cooked_at

        The recipes.total_times_cooked is updated automatically by database trigger.

        Args:
            user_id: User ID
            recipe_id: Recipe ID
            rating: Optional rating given at this cooking session (0.5-5.0)
            image_url: Optional URL to photo taken during cooking
            duration_minutes: Optional actual cooking time in minutes
        """
        try:
            # Get current data
            current = await self.get_by_user_and_recipe(user_id, recipe_id)

            times_cooked = (current["times_cooked"] if current else 0) + 1
            now = datetime.now(timezone.utc).isoformat()

            # Build cooking event data
            cooking_event_data = {
                "user_id": user_id,
                "recipe_id": recipe_id,
                "cooked_at": now
            }

            # Add optional session data
            if rating is not None:
                cooking_event_data["rating"] = rating
            if image_url is not None:
                cooking_event_data["image_url"] = image_url
            if duration_minutes is not None:
                cooking_event_data["duration_minutes"] = duration_minutes

            # Insert cooking event for time-based analytics and history
            self.supabase.table("recipe_cooking_events")\
                .insert(cooking_event_data)\
                .execute()

            # Build user_recipe_data update
            user_data_update = {
                "times_cooked": times_cooked,
                "last_cooked_at": now
            }

            # If rating was provided, update the user's current rating for this recipe
            if rating is not None:
                user_data_update["rating"] = rating

            # Upsert with incremented count and optional rating
            return await self.upsert_user_data(
                user_id,
                recipe_id,
                user_data_update
            )
        except Exception as e:
            logger.error(f"Error incrementing cooked count: {str(e)}")
            raise

    async def get_previous_rating(
        self,
        user_id: str,
        recipe_id: str
    ) -> Optional[float]:
        """
        Get user's previous rating for a recipe (supports half-stars).

        Returns:
            Previous rating (0.5-5.0 in 0.5 increments) or None if no previous rating exists
        """
        try:
            user_data = await self.get_by_user_and_recipe(user_id, recipe_id)
            return user_data.get("rating") if user_data else None
        except Exception as e:
            logger.error(f"Error fetching previous rating: {str(e)}")
            raise

    # =============================================
    # Collection-related methods (virtual collections)
    # =============================================

    async def get_user_extracted_recipes(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recipes that the user has extracted.

        Returns user_recipe_data records with full recipe details
        where was_extracted = true.
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*, recipes!inner(*)")\
                .eq("user_id", user_id)\
                .eq("was_extracted", True)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user extracted recipes: {str(e)}")
            raise

    async def count_user_extracted_recipes(self, user_id: str) -> int:
        """Count recipes that the user has extracted."""
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("was_extracted", True)\
                .execute()

            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting user extracted recipes: {str(e)}")
            raise

    async def count_user_favorites(self, user_id: str) -> int:
        """Count recipes that the user has favorited."""
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("is_favorite", True)\
                .execute()

            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting user favorites: {str(e)}")
            raise

    async def mark_as_extracted(
        self,
        user_id: str,
        recipe_id: str
    ) -> Dict[str, Any]:
        """
        Mark a recipe as extracted by this user.

        This is used when:
        1. User extracts a new recipe
        2. User extracts a duplicate (recipe already exists)

        Uses upsert to handle both new and existing records.
        """
        try:
            return await self.upsert_user_data(
                user_id,
                recipe_id,
                {"was_extracted": True}
            )
        except Exception as e:
            logger.error(f"Error marking recipe as extracted: {str(e)}")
            raise

    async def set_favorite(
        self,
        user_id: str,
        recipe_id: str,
        is_favorite: bool
    ) -> Dict[str, Any]:
        """
        Set the favorite status for a recipe.

        Args:
            user_id: User ID
            recipe_id: Recipe ID
            is_favorite: True to favorite, False to unfavorite
        """
        try:
            return await self.upsert_user_data(
                user_id,
                recipe_id,
                {"is_favorite": is_favorite}
            )
        except Exception as e:
            logger.error(f"Error setting favorite status: {str(e)}")
            raise

    # =============================================
    # Cooking Event CRUD methods
    # =============================================

    async def get_cooking_event(
        self,
        event_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific cooking event by ID.
        Verifies ownership by checking user_id.

        Returns:
            The cooking event if found and owned by user, None otherwise
        """
        try:
            response = self.supabase.table("recipe_cooking_events")\
                .select("*")\
                .eq("id", event_id)\
                .eq("user_id", user_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching cooking event: {str(e)}")
            raise

    async def update_cooking_event(
        self,
        event_id: str,
        user_id: str,
        cooked_at: Optional[datetime] = None,
        rating: Optional[float] = None,
        image_url: Optional[str] = None,
        remove_image: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Update a cooking event.
        Only the owner can update their own events.

        Args:
            event_id: The cooking event ID
            user_id: The user ID (for ownership verification)
            cooked_at: New timestamp for when cooking happened
            rating: New rating (0.5-5.0)
            image_url: New image URL (or None to keep existing)
            remove_image: If True, remove the existing image

        Returns:
            Updated cooking event, or None if not found/not owned
        """
        try:
            # First verify ownership
            existing = await self.get_cooking_event(event_id, user_id)
            if not existing:
                return None

            # Build update data
            update_data = {}
            if cooked_at is not None:
                update_data["cooked_at"] = cooked_at.isoformat()
            if rating is not None:
                update_data["rating"] = rating
            if remove_image:
                update_data["image_url"] = None
            elif image_url is not None:
                update_data["image_url"] = image_url

            if not update_data:
                # No changes to make
                return existing

            response = self.supabase.table("recipe_cooking_events")\
                .update(update_data)\
                .eq("id", event_id)\
                .eq("user_id", user_id)\
                .execute()

            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating cooking event: {str(e)}")
            raise

    async def delete_cooking_event(
        self,
        event_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Delete a cooking event and decrement times_cooked.

        Args:
            event_id: The cooking event ID
            user_id: The user ID (for ownership verification)

        Returns:
            The deleted event data (including image_url for cleanup), or None if not found
        """
        try:
            # First get the event to verify ownership and get recipe_id
            existing = await self.get_cooking_event(event_id, user_id)
            if not existing:
                return None

            recipe_id = existing["recipe_id"]

            # Delete the event
            self.supabase.table("recipe_cooking_events")\
                .delete()\
                .eq("id", event_id)\
                .eq("user_id", user_id)\
                .execute()

            # Decrement times_cooked in user_recipe_data
            user_data = await self.get_by_user_and_recipe(user_id, recipe_id)
            if user_data and user_data.get("times_cooked", 0) > 0:
                new_count = user_data["times_cooked"] - 1
                await self.upsert_user_data(
                    user_id,
                    recipe_id,
                    {"times_cooked": new_count}
                )

            return existing
        except Exception as e:
            logger.error(f"Error deleting cooking event: {str(e)}")
            raise
