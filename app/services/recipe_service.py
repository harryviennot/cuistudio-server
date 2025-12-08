"""
Recipe service for business logic
"""
from typing import Optional, Dict, Any
from supabase import Client
import logging

from app.repositories.recipe_repository import RecipeRepository
from app.repositories.user_recipe_repository import UserRecipeRepository

logger = logging.getLogger(__name__)


class RecipeService:
    """Service for recipe business logic"""

    def __init__(self, supabase: Client):
        # Use single client (admin) for all operations
        # User authentication is already validated at the endpoint level
        self.recipe_repo = RecipeRepository(supabase)
        self.user_recipe_repo = UserRecipeRepository(supabase)

    async def update_recipe_timings(
        self,
        recipe_id: str,
        user_id: str,
        prep_time_minutes: Optional[int] = None,
        cook_time_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Smart timing update with ownership logic.

        If user owns the recipe:
            - Updates base recipe timings (benefits all users)
            - Returns updated_base_recipe: true

        If user doesn't own the recipe:
            - Updates user's personal custom timings
            - Returns updated_base_recipe: false

        Args:
            recipe_id: Recipe to update
            user_id: Current user ID
            prep_time_minutes: Preparation time in minutes
            cook_time_minutes: Cooking time in minutes

        Returns:
            Dictionary with timing data and ownership indicator
        """
        try:
            # Get recipe to check ownership
            recipe = await self.recipe_repo.get_by_id(recipe_id)
            if not recipe:
                raise ValueError(f"Recipe {recipe_id} not found")

            is_owner = recipe["created_by"] == user_id

            if is_owner:
                # User owns recipe - update base recipe
                update_data = {}
                if prep_time_minutes is not None:
                    update_data["prep_time_minutes"] = prep_time_minutes
                if cook_time_minutes is not None:
                    update_data["cook_time_minutes"] = cook_time_minutes

                # Calculate total time
                final_prep = prep_time_minutes if prep_time_minutes is not None else recipe.get("prep_time_minutes", 0)
                final_cook = cook_time_minutes if cook_time_minutes is not None else recipe.get("cook_time_minutes", 0)
                update_data["total_time_minutes"] = (final_prep or 0) + (final_cook or 0)

                updated_recipe = await self.recipe_repo.update(recipe_id, update_data)

                return {
                    "prep_time_minutes": updated_recipe.get("prep_time_minutes"),
                    "cook_time_minutes": updated_recipe.get("cook_time_minutes"),
                    "total_time_minutes": updated_recipe.get("total_time_minutes"),
                    "updated_base_recipe": True
                }
            else:
                # User doesn't own recipe - update user customization
                update_data = {}
                if prep_time_minutes is not None:
                    update_data["custom_prep_time_minutes"] = prep_time_minutes
                if cook_time_minutes is not None:
                    update_data["custom_cook_time_minutes"] = cook_time_minutes

                user_data = await self.user_recipe_repo.upsert_user_data(
                    user_id,
                    recipe_id,
                    update_data
                )

                # Calculate total from custom or base values
                final_prep = user_data.get("custom_prep_time_minutes") or recipe.get("prep_time_minutes", 0)
                final_cook = user_data.get("custom_cook_time_minutes") or recipe.get("cook_time_minutes", 0)

                return {
                    "prep_time_minutes": user_data.get("custom_prep_time_minutes") or recipe.get("prep_time_minutes"),
                    "cook_time_minutes": user_data.get("custom_cook_time_minutes") or recipe.get("cook_time_minutes"),
                    "total_time_minutes": (final_prep or 0) + (final_cook or 0),
                    "updated_base_recipe": False
                }

        except Exception as e:
            logger.error(f"Error updating recipe timings: {str(e)}")
            raise

    async def update_recipe_rating(
        self,
        recipe_id: str,
        user_id: str,
        rating: float
    ) -> None:
        """
        Update recipe rating with automatic aggregation.

        Updates user's personal rating and recalculates recipe average rating,
        rating count, and distribution.

        This method updates both user_recipe_data and recipes tables.
        Note: Supabase REST API doesn't support explicit transactions,
        but operations are ordered to minimize inconsistency risk.

        Args:
            recipe_id: Recipe to rate
            user_id: Current user ID
            rating: Rating value (0.5, 1.0, 1.5, ..., 5.0)

        Raises:
            ValueError: If rating is invalid
            Exception: If update fails
        """
        try:
            # Validate rating is in half-star increments
            if rating < 0.5 or rating > 5.0:
                raise ValueError("Rating must be between 0.5 and 5.0")
            if (rating * 2) != int(rating * 2):
                raise ValueError("Rating must be in half-star increments (0.5, 1.0, 1.5, ...)")

            # Get previous rating if exists (needed for aggregate calculation)
            previous_rating = await self.user_recipe_repo.get_previous_rating(user_id, recipe_id)

            # Update user's personal rating first
            user_data = await self.user_recipe_repo.upsert_user_data(
                user_id,
                recipe_id,
                {"rating": rating}
            )

            if not user_data:
                raise ValueError(f"Failed to update user rating for recipe {recipe_id}")

            # Update recipe aggregate stats
            # If this fails, user rating is already saved but aggregates will be stale
            # This is acceptable as aggregates can be recalculated
            updated_recipe = await self.recipe_repo.update_rating_stats(
                recipe_id,
                rating,
                previous_rating
            )

            if not updated_recipe:
                logger.error(f"Failed to update rating stats for recipe {recipe_id} after user rating was saved")
                raise ValueError(f"Failed to update rating stats for recipe {recipe_id}")

        except Exception as e:
            logger.error(f"Error updating recipe rating: {str(e)}")
            raise
