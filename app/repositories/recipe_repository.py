"""
Recipe repository for database operations
"""
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, urlunparse
from supabase import Client
import logging

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class RecipeRepository(BaseRepository):
    """Repository for recipe operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "recipes")

    async def enrich_with_category(
        self,
        recipes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich recipe(s) with category data (id and slug only).

        Frontend handles translation via i18n files using the slug as the key.

        Args:
            recipes: List of recipe dicts with category_id field

        Returns:
            Recipes with 'category' object added (id, slug)
        """
        if not recipes:
            return recipes

        # Collect unique category IDs
        category_ids = list(set(
            r["category_id"] for r in recipes
            if r.get("category_id")
        ))

        if not category_ids:
            # No categories to fetch, return recipes as-is
            for recipe in recipes:
                recipe["category"] = None
            return recipes

        try:
            # Fetch categories (no translations - frontend handles i18n)
            response = self.supabase.table("categories")\
                .select("id, slug")\
                .in_("id", category_ids)\
                .execute()

            # Build category lookup
            category_lookup = {
                cat["id"]: {"id": cat["id"], "slug": cat["slug"]}
                for cat in response.data or []
            }

            # Enrich recipes
            for recipe in recipes:
                cat_id = recipe.get("category_id")
                recipe["category"] = category_lookup.get(cat_id) if cat_id else None

            return recipes
        except Exception as e:
            logger.warning(f"Failed to enrich recipes with category: {e}")
            # Return recipes without category enrichment
            for recipe in recipes:
                recipe["category"] = None
            return recipes

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize a URL for duplicate detection.

        Removes query parameters, fragments, and trailing slashes.
        Converts to lowercase for consistent comparison.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL string
        """
        if not url:
            return url
        try:
            parsed = urlparse(url.lower().strip())
            # Remove query params, fragments, and normalize path
            path = parsed.path.rstrip('/')
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc,
                path,
                '',  # params
                '',  # query
                ''   # fragment
            ))
            return normalized
        except Exception:
            return url.lower().strip()

    async def find_by_source_url(self, source_url: str) -> Optional[Dict[str, Any]]:
        """
        Find a recipe by its source URL for duplicate detection.

        Normalizes the URL before searching to handle variations
        (query params, trailing slashes, etc.).

        Args:
            source_url: URL to search for

        Returns:
            Recipe dict with id, title, image_url, is_public, created_by
            or None if not found
        """
        try:
            normalized_url = self.normalize_url(source_url)

            # Search for recipes with matching source_url
            # We check both the exact URL and normalized versions
            response = self.supabase.table(self.table_name)\
                .select("id, title, image_url, is_public, created_by, source_url")\
                .eq("is_draft", False)\
                .not_.is_("source_url", "null")\
                .execute()

            # Check each recipe's normalized URL
            for recipe in response.data or []:
                if recipe.get("source_url"):
                    if self.normalize_url(recipe["source_url"]) == normalized_url:
                        return {
                            "recipe_id": recipe["id"],
                            "title": recipe.get("title"),
                            "image_url": recipe.get("image_url"),
                            "is_public": recipe.get("is_public"),
                            "created_by": recipe.get("created_by")
                        }

            return None
        except Exception as e:
            logger.error(f"Error finding recipe by source URL: {str(e)}")
            return None

    async def get_with_contributors(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get recipe with contributor information"""
        try:
            # Get recipe
            recipe = await self.get_by_id(recipe_id)
            if not recipe:
                return None

            # Get contributors
            contributors_response = self.supabase.table("recipe_contributors")\
                .select("*")\
                .eq("recipe_id", recipe_id)\
                .order("order")\
                .execute()

            recipe["contributors"] = contributors_response.data or []
            return recipe
        except Exception as e:
            logger.error(f"Error fetching recipe with contributors: {str(e)}")
            raise

    async def get_user_recipes(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        include_public: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get recipes created by a user

        Optimized to select only fields needed for list view (excludes heavy JSONB arrays)
        """
        try:
            # Select only fields needed for list view (excludes ingredients & instructions)
            query = self.supabase.table(self.table_name)\
                .select("""
                    id, title, description, image_url,
                    servings, difficulty, tags, category_id,
                    prep_time_minutes, cook_time_minutes, total_time_minutes,
                    created_by, is_public, fork_count,
                    average_rating, rating_count, total_times_cooked,
                    created_at, source_type
                """)\
                .eq("created_by", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user recipes: {str(e)}")
            raise

    async def get_public_recipes(
        self,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get public recipes with optional filters"""
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("is_public", True)\
                .eq("is_draft", False)\
                .order("created_at", desc=True)

            # Apply additional filters
            if filters:
                if "difficulty" in filters:
                    query = query.eq("difficulty", filters["difficulty"])
                if "tags" in filters and filters["tags"]:
                    query = query.contains("tags", filters["tags"])
                # Filter by category_id (UUID)
                if "category_id" in filters and filters["category_id"]:
                    query = query.eq("category_id", filters["category_id"])

            response = query.limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching public recipes: {str(e)}")
            raise

    async def search_recipes(
        self,
        user_id: Optional[str],
        search_query: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search recipes using PostgreSQL full-text search with language-aware dictionaries.

        Uses ts_rank for relevance scoring and plainto_tsquery for natural language queries.
        Results are sorted by relevance (highest first).

        Args:
            user_id: Optional user ID to include user's own recipes
            search_query: Natural language search query (e.g., "chicken pasta", "grilled vegetables")
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination

        Returns:
            List of recipes sorted by relevance score
        """
        try:
            # Use RPC to call a custom function for full-text search with ranking
            # This allows us to use ts_rank and plainto_tsquery which aren't directly
            # available in Supabase's query builder

            # Build the RPC call
            response = self.supabase.rpc(
                'search_recipes_full_text',
                {
                    'search_query': search_query,
                    'user_id_param': user_id,
                    'limit_param': limit,
                    'offset_param': offset
                }
            ).execute()

            results = response.data or []
            logger.info(f"Full-text search for '{search_query}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching recipes with full-text search: {str(e)}")
            # Fallback to basic search if full-text search fails
            logger.info("Falling back to basic ilike search")
            try:
                query = self.supabase.table(self.table_name)\
                    .select("""
                        id, title, description, image_url,
                        servings, difficulty, tags, category_id,
                        prep_time_minutes, cook_time_minutes, total_time_minutes,
                        resting_time_minutes, created_by, is_public, fork_count,
                        average_rating, rating_count, total_times_cooked,
                        created_at, source_type
                    """)\
                    .or_(f"title.ilike.%{search_query}%,description.ilike.%{search_query}%")

                # Include public recipes and user's own recipes
                if user_id:
                    query = query.or_(f"is_public.eq.true,created_by.eq.{user_id}")
                else:
                    query = query.eq("is_public", True)

                response = query.limit(limit).offset(offset).execute()
                return response.data or []
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {str(fallback_error)}")
                raise

    async def search_recipes_filtered(
        self,
        user_id: Optional[str],
        search_query: str,
        limit: int = 20,
        offset: int = 0,
        difficulty: Optional[str] = None,
        category_ids: Optional[List[str]] = None,
        max_prep_time: Optional[int] = None,
        max_cook_time: Optional[int] = None,
        max_rest_time: Optional[int] = None,
        min_time: Optional[int] = None,
        max_time: Optional[int] = None,
        sort_by: str = "relevance",
        library_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search recipes with filters and sorting options.

        This method extends the basic search_recipes() with additional filtering
        capabilities and flexible sorting options.

        Args:
            user_id: Optional user ID to include user's own recipes and library filtering
            search_query: Natural language search query
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination
            difficulty: Filter by difficulty level ("easy", "medium", "hard")
            category_ids: Filter by category UUIDs (OR logic - recipe matches ANY category)
            max_prep_time: Maximum prep time in minutes
            max_cook_time: Maximum cook time in minutes
            max_rest_time: Maximum resting time in minutes
            min_time: Minimum total_time_minutes (legacy)
            max_time: Maximum total_time_minutes (legacy)
            sort_by: Sort option ("relevance", "recent", "rating", "cook_count", "time")
            library_only: If True, only return user's library recipes (favorites or extracted)

        Returns:
            List of recipes matching filters, sorted by the specified option
        """
        try:
            # First, get results from basic full-text search
            recipes = await self.search_recipes(user_id, search_query, limit=100, offset=0)

            # If library_only, we need to fetch user_recipe_data to filter
            if library_only and user_id:
                # Get all recipe IDs from search results
                recipe_ids = [r["id"] for r in recipes]

                if not recipe_ids:
                    return []

                # Fetch user_recipe_data for these recipes
                user_data_response = self.supabase.table("user_recipe_data")\
                    .select("recipe_id, is_favorite, was_extracted")\
                    .eq("user_id", user_id)\
                    .in_("recipe_id", recipe_ids)\
                    .execute()

                # Create set of library recipe IDs (favorites, extracted, or created by user)
                library_recipe_ids = set()
                for row in (user_data_response.data or []):
                    if row.get("is_favorite") or row.get("was_extracted"):
                        library_recipe_ids.add(row["recipe_id"])

                # Also include recipes created by the user
                for recipe in recipes:
                    if recipe.get("created_by") == user_id:
                        library_recipe_ids.add(recipe["id"])

                # Filter recipes to only library items
                recipes = [r for r in recipes if r["id"] in library_recipe_ids]

            # Apply difficulty filter
            if difficulty:
                recipes = [r for r in recipes if r.get("difficulty") == difficulty]

            # Apply category filter (OR logic - recipe matches ANY of the categories)
            if category_ids:
                recipes = [r for r in recipes if r.get("category_id") in category_ids]

            # Apply granular time filters (AND logic - each enabled filter must pass)
            if max_prep_time is not None:
                recipes = [r for r in recipes
                           if r.get("prep_time_minutes") is None
                           or r["prep_time_minutes"] <= max_prep_time]

            if max_cook_time is not None:
                recipes = [r for r in recipes
                           if r.get("cook_time_minutes") is None
                           or r["cook_time_minutes"] <= max_cook_time]

            if max_rest_time is not None:
                recipes = [r for r in recipes
                           if r.get("resting_time_minutes") is None
                           or r["resting_time_minutes"] <= max_rest_time]

            # Apply legacy total time filters (for backward compatibility)
            if min_time is not None:
                recipes = [r for r in recipes if r.get("total_time_minutes") and r["total_time_minutes"] >= min_time]

            if max_time is not None:
                recipes = [r for r in recipes if r.get("total_time_minutes") and r["total_time_minutes"] <= max_time]

            # Apply sorting
            if sort_by == "recent":
                # Sort by created_at DESC
                recipes.sort(key=lambda r: r.get("created_at", ""), reverse=True)
            elif sort_by == "rating":
                # Sort by average_rating DESC, then rating_count DESC
                recipes.sort(
                    key=lambda r: (
                        r.get("average_rating") or 0,
                        r.get("rating_count") or 0
                    ),
                    reverse=True
                )
            elif sort_by == "cook_count":
                # Sort by total_times_cooked DESC
                recipes.sort(key=lambda r: r.get("total_times_cooked", 0), reverse=True)
            elif sort_by == "time":
                # Sort by total_time_minutes ASC (quickest first)
                # Put recipes with no time at the end
                recipes_with_time = [r for r in recipes if r.get("total_time_minutes")]
                recipes_without_time = [r for r in recipes if not r.get("total_time_minutes")]
                recipes_with_time.sort(key=lambda r: r["total_time_minutes"])
                recipes = recipes_with_time + recipes_without_time
            # else: sort_by == "relevance" - already sorted by RPC function

            # Apply pagination after filtering and sorting
            return recipes[offset:offset + limit]

        except Exception as e:
            logger.error(f"Error in search_recipes_filtered: {str(e)}")
            raise

    async def fork_recipe(
        self,
        original_recipe_id: str,
        new_recipe_data: Dict[str, Any],
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fork a recipe (create a copy with attribution)"""
        try:
            # Get original recipe
            original = await self.get_by_id(original_recipe_id)
            if not original:
                return None

            # Create forked recipe
            forked_recipe = await self.create(new_recipe_data)
            if not forked_recipe:
                return None

            # Update fork count on original
            await self.supabase.table(self.table_name)\
                .update({"fork_count": original["fork_count"] + 1})\
                .eq("id", original_recipe_id)\
                .execute()

            # Get original contributors
            original_contributors = self.supabase.table("recipe_contributors")\
                .select("*")\
                .eq("recipe_id", original_recipe_id)\
                .order("order")\
                .execute()

            # Add contributors to forked recipe
            contributors = []
            order = 0

            # Add original contributors
            if original_contributors.data:
                for contrib in original_contributors.data:
                    contributors.append({
                        "recipe_id": forked_recipe["id"],
                        "user_id": contrib["user_id"],
                        "contribution_type": contrib["contribution_type"],
                        "order": order
                    })
                    order += 1

            # Add current user as fork contributor
            contributors.append({
                "recipe_id": forked_recipe["id"],
                "user_id": user_id,
                "contribution_type": "fork",
                "order": order
            })

            # Insert all contributors
            if contributors:
                self.supabase.table("recipe_contributors").insert(contributors).execute()

            return forked_recipe
        except Exception as e:
            logger.error(f"Error forking recipe: {str(e)}")
            raise

    async def get_recipe_forks(self, recipe_id: str) -> List[Dict[str, Any]]:
        """Get all forks of a recipe"""
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("original_recipe_id", recipe_id)\
                .eq("is_public", True)\
                .order("created_at", desc=True)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching recipe forks: {str(e)}")
            raise

    async def increment_fork_count(self, recipe_id: str) -> bool:
        """Increment fork count for a recipe"""
        try:
            recipe = await self.get_by_id(recipe_id)
            if not recipe:
                return False

            await self.update(recipe_id, {"fork_count": recipe["fork_count"] + 1})
            return True
        except Exception as e:
            logger.error(f"Error incrementing fork count: {str(e)}")
            raise

    async def update_rating_stats(
        self,
        recipe_id: str,
        new_rating: float,
        previous_rating: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update recipe rating statistics atomically with half-star support.

        Args:
            recipe_id: Recipe to update
            new_rating: New rating value (0.5, 1.0, 1.5, ..., 5.0)
            previous_rating: Previous rating value if user is updating their rating

        Returns:
            Updated recipe with new rating stats
        """
        try:
            recipe = await self.get_by_id(recipe_id)
            if not recipe:
                return None

            # Get current distribution (supports half-star ratings)
            distribution = recipe.get("rating_distribution", {
                "0.5": 0, "1": 0, "1.5": 0, "2": 0, "2.5": 0,
                "3": 0, "3.5": 0, "4": 0, "4.5": 0, "5": 0
            })

            # Update distribution
            if previous_rating:
                # User is changing their rating - remove old, add new
                prev_key = str(previous_rating) if previous_rating % 1 != 0 else str(int(previous_rating))
                new_key = str(new_rating) if new_rating % 1 != 0 else str(int(new_rating))
                distribution[prev_key] = max(0, distribution.get(prev_key, 0) - 1)
                distribution[new_key] = distribution.get(new_key, 0) + 1
            else:
                # New rating - just add
                new_key = str(new_rating) if new_rating % 1 != 0 else str(int(new_rating))
                distribution[new_key] = distribution.get(new_key, 0) + 1

            # Calculate new average with half-star precision
            total_ratings = sum(distribution.values())
            if total_ratings == 0:
                average_rating = None
            else:
                weighted_sum = sum(float(stars) * count for stars, count in distribution.items())
                average_rating = round(weighted_sum / total_ratings, 2)

            # Update recipe
            update_data = {
                "average_rating": average_rating,
                "rating_count": total_ratings,
                "rating_distribution": distribution
            }

            updated_recipe = await self.update(recipe_id, update_data)
            return updated_recipe
        except Exception as e:
            logger.error(f"Error updating rating stats: {str(e)}")
            raise

    async def get_trending_recipes(
        self,
        time_window_days: int = 7,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get trending recipes based on cooking frequency in a time window.

        Args:
            time_window_days: Number of days to look back (default: 7 for "this week")
            limit: Maximum number of recipes to return
            offset: Number of results to skip for pagination

        Returns:
            List of recipes with cooking statistics, ordered by popularity
        """
        try:
            # Use the database function for optimized trending query
            response = self.supabase.rpc(
                'get_trending_recipes',
                {
                    'time_window_days': time_window_days,
                    'limit_param': limit,
                    'offset_param': offset
                }
            ).execute()

            trending_recipe_ids = response.data or []

            if not trending_recipe_ids:
                return []

            # Fetch full recipe details for trending recipes
            recipe_ids = [item['recipe_id'] for item in trending_recipe_ids]

            recipes_response = self.supabase.table(self.table_name)\
                .select("*")\
                .in_("id", recipe_ids)\
                .execute()

            recipes = recipes_response.data or []

            # Merge cooking stats with recipe data
            recipes_with_stats = []
            for recipe in recipes:
                # Find corresponding stats
                stats = next(
                    (item for item in trending_recipe_ids if item['recipe_id'] == recipe['id']),
                    None
                )
                if stats:
                    recipe['cooking_stats'] = {
                        'cook_count': stats['cook_count'],
                        'unique_users': stats['unique_users'],
                        'time_window_days': time_window_days
                    }
                    recipes_with_stats.append(recipe)

            # Sort by cook count (maintain trending order)
            recipes_with_stats.sort(
                key=lambda x: x['cooking_stats']['cook_count'],
                reverse=True
            )

            return recipes_with_stats
        except Exception as e:
            logger.error(f"Error fetching trending recipes: {str(e)}")
            raise

    async def get_user_cooking_history(
        self,
        user_id: str,
        time_window_days: int = 30,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get a user's cooking history in a time window.

        Args:
            user_id: User ID to get history for
            time_window_days: Number of days to look back (default: 30)
            limit: Maximum number of recipes to return
            offset: Number of results to skip for pagination

        Returns:
            List of recipes the user has cooked with cooking statistics
        """
        try:
            response = self.supabase.rpc(
                'get_user_cooking_history',
                {
                    'user_id_param': user_id,
                    'time_window_days': time_window_days,
                    'limit_param': limit,
                    'offset_param': offset
                }
            ).execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user cooking history: {str(e)}")
            raise

    async def get_most_extracted_recipes(
        self,
        source_category: str,
        limit: int = 8,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get most extracted public recipes by source category.

        Args:
            source_category: 'video' for social media (TikTok, Instagram, YouTube),
                           'website' for recipe websites/URLs
            limit: Maximum number of recipes to return
            offset: Number of results to skip for pagination

        Returns:
            List of recipes with extraction statistics, ordered by extraction count
        """
        try:
            # First, get extraction counts per recipe from user_recipe_data
            # We need to count recipes that were extracted by multiple users

            if source_category == "video":
                # Video sources: recipes that have a video_sources record
                # Use RPC to execute the query (Supabase Python doesn't support complex joins well)
                response = self.supabase.rpc(
                    'get_most_extracted_video_recipes',
                    {
                        'limit_param': limit,
                        'offset_param': offset
                    }
                ).execute()
            else:
                # Website sources: recipes with source_type='link' that do NOT have video_sources
                response = self.supabase.rpc(
                    'get_most_extracted_website_recipes',
                    {
                        'limit_param': limit,
                        'offset_param': offset
                    }
                ).execute()

            extracted_recipe_ids = response.data or []

            if not extracted_recipe_ids:
                return []

            # Fetch full recipe details
            recipe_ids = [item['recipe_id'] for item in extracted_recipe_ids]

            recipes_response = self.supabase.table(self.table_name)\
                .select("*")\
                .in_("id", recipe_ids)\
                .execute()

            recipes = recipes_response.data or []

            # Merge extraction stats with recipe data
            recipes_with_stats = []
            for recipe in recipes:
                stats = next(
                    (item for item in extracted_recipe_ids if item['recipe_id'] == recipe['id']),
                    None
                )
                if stats:
                    recipe['extraction_stats'] = {
                        'extraction_count': stats['extraction_count'],
                        'unique_extractors': stats['unique_extractors']
                    }
                    recipes_with_stats.append(recipe)

            # Sort by extraction count (maintain order)
            recipes_with_stats.sort(
                key=lambda x: x['extraction_stats']['extraction_count'],
                reverse=True
            )

            return recipes_with_stats
        except Exception as e:
            logger.error(f"Error fetching most extracted recipes: {str(e)}")
            raise

    async def get_highest_rated_recipes(
        self,
        min_rating_count: int = 3,
        limit: int = 8,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get highest rated public recipes.

        Args:
            min_rating_count: Minimum number of ratings required
            limit: Maximum number of recipes to return
            offset: Number of results to skip for pagination

        Returns:
            List of recipes ordered by average rating (highest first)
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("is_public", True)\
                .eq("is_draft", False)\
                .gte("rating_count", min_rating_count)\
                .order("average_rating", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching highest rated recipes: {str(e)}")
            raise

    async def get_recent_public_recipes(
        self,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recently added public recipes.

        Args:
            limit: Maximum number of recipes to return
            offset: Number of results to skip for pagination

        Returns:
            List of recipes ordered by creation date (newest first)
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("is_public", True)\
                .eq("is_draft", False)\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching recent public recipes: {str(e)}")
            raise

    async def get_popular_recipes(
        self,
        category_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get popular public recipes with optional category filter.

        Popularity is calculated as: (average_rating * rating_count) + total_times_cooked
        This balances rating quality with engagement metrics.

        Args:
            category_id: Optional UUID to filter by category
            limit: Maximum number of recipes to return
            offset: Number of results to skip for pagination

        Returns:
            List of recipes ordered by popularity score (highest first)
        """
        try:
            response = self.supabase.rpc(
                'get_popular_recipes',
                {
                    'category_id_param': category_id,
                    'limit_param': limit,
                    'offset_param': offset
                }
            ).execute()

            recipes = response.data or []

            # Enrich with category data
            recipes = await self.enrich_with_category(recipes)

            return recipes
        except Exception as e:
            logger.error(f"Error fetching popular recipes: {str(e)}")
            raise
