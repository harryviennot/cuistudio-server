"""
Repository for user collections
"""
from typing import Optional, List, Dict, Any
from supabase import Client
import logging
import re

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CollectionRepository(BaseRepository):
    """Repository for user collection operations"""

    def __init__(self, supabase: Client):
        super().__init__(supabase, "user_collections")

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name"""
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    async def create_collection(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        is_system: bool = False,
        sort_order: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new collection for a user.

        Args:
            user_id: User ID
            name: Collection name
            description: Optional description
            is_system: Whether this is a system collection (cannot be deleted)
            sort_order: Display order

        Returns:
            Created collection or None if failed
        """
        try:
            slug = self._generate_slug(name)
            data = {
                "user_id": user_id,
                "name": name,
                "slug": slug,
                "description": description,
                "is_system": is_system,
                "sort_order": sort_order
            }
            response = self.supabase.table(self.table_name).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            # Check if it's a duplicate slug
            if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                logger.info(f"Collection with slug '{slug}' already exists for user {user_id}")
                return None
            logger.error(f"Error creating collection: {str(e)}")
            raise

    async def get_user_collections(
        self,
        user_id: str,
        include_recipe_count: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all collections for a user.

        Args:
            user_id: User ID
            include_recipe_count: Whether to include recipe counts

        Returns:
            List of collections
        """
        try:
            if include_recipe_count:
                # Use a subquery to get counts
                response = self.supabase.table(self.table_name)\
                    .select("*, collection_recipes(count)")\
                    .eq("user_id", user_id)\
                    .order("sort_order")\
                    .execute()

                # Transform the response to include recipe_count
                collections = []
                for item in response.data or []:
                    collection = {**item}
                    # Extract count from nested collection_recipes
                    if "collection_recipes" in collection:
                        collection["recipe_count"] = len(collection.pop("collection_recipes"))
                    else:
                        collection["recipe_count"] = 0
                    collections.append(collection)
                return collections
            else:
                response = self.supabase.table(self.table_name)\
                    .select("*")\
                    .eq("user_id", user_id)\
                    .order("sort_order")\
                    .execute()
                return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user collections: {str(e)}")
            raise

    async def get_by_slug(self, user_id: str, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get a collection by user ID and slug.

        Args:
            user_id: User ID
            slug: Collection slug

        Returns:
            Collection or None if not found
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("slug", slug)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching collection by slug: {str(e)}")
            raise

    async def update_collection(
        self,
        collection_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a collection (only non-system collections).

        Args:
            collection_id: Collection ID
            user_id: User ID (for ownership check)
            name: New name (optional)
            description: New description (optional)

        Returns:
            Updated collection or None if not found/not allowed
        """
        try:
            # First check if collection exists and is not system
            existing = await self.get_by_id(collection_id)
            if not existing:
                return None
            if existing["user_id"] != user_id:
                raise PermissionError("You don't own this collection")
            if existing["is_system"]:
                raise PermissionError("Cannot modify system collections")

            update_data = {}
            if name is not None:
                update_data["name"] = name
                update_data["slug"] = self._generate_slug(name)
            if description is not None:
                update_data["description"] = description

            if not update_data:
                return existing

            response = self.supabase.table(self.table_name)\
                .update(update_data)\
                .eq("id", collection_id)\
                .execute()
            return response.data[0] if response.data else None
        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Error updating collection: {str(e)}")
            raise

    async def delete_collection(self, collection_id: str, user_id: str) -> bool:
        """
        Delete a collection (only non-system collections).

        Args:
            collection_id: Collection ID
            user_id: User ID (for ownership check)

        Returns:
            True if deleted, False if not found/not allowed
        """
        try:
            # First check if collection exists and is not system
            existing = await self.get_by_id(collection_id)
            if not existing:
                return False
            if existing["user_id"] != user_id:
                raise PermissionError("You don't own this collection")
            if existing["is_system"]:
                raise PermissionError("Cannot delete system collections")

            response = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", collection_id)\
                .execute()
            return len(response.data) > 0
        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise

    async def create_default_collections(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Create default system collections for a new user.

        Args:
            user_id: User ID

        Returns:
            List of created collections
        """
        try:
            collections = []

            # Create "Extracted" collection
            extracted = await self.create_collection(
                user_id=user_id,
                name="Extracted",
                description="Recipes you've extracted",
                is_system=True,
                sort_order=0
            )
            if extracted:
                collections.append(extracted)

            # Create "Saved" collection
            saved = await self.create_collection(
                user_id=user_id,
                name="Saved",
                description="Recipes saved from others",
                is_system=True,
                sort_order=1
            )
            if saved:
                collections.append(saved)

            return collections
        except Exception as e:
            logger.error(f"Error creating default collections: {str(e)}")
            raise
