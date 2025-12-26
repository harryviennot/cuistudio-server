"""
Base repository with common database operations
"""
from typing import Optional, List, Dict, Any, TypeVar, Generic
from supabase import Client
import logging

T = TypeVar('T')
logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations"""

    def __init__(self, supabase: Client, table_name: str):
        self.supabase = supabase
        self.table_name = table_name

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new record"""
        try:
            response = self.supabase.table(self.table_name).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating record in {self.table_name}: {str(e)}")
            raise

    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a record by ID"""
        try:
            response = self.supabase.table(self.table_name).select("*").eq("id", record_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching record from {self.table_name}: {str(e)}")
            raise

    async def update(self, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record by ID"""
        try:
            logger.info(f"[BASE REPO] Updating {self.table_name} id={record_id} with data keys: {list(data.keys())}")
            if "category_id" in data:
                logger.info(f"[BASE REPO] category_id value being sent: {data['category_id']}")
            response = self.supabase.table(self.table_name).update(data).eq("id", record_id).execute()
            logger.info(f"[BASE REPO] Update response data: {response.data}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating record in {self.table_name}: {str(e)}")
            raise

    async def delete(self, record_id: str) -> bool:
        """Delete a record by ID"""
        try:
            response = self.supabase.table(self.table_name).delete().eq("id", record_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting record from {self.table_name}: {str(e)}")
            raise

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """List records with optional filtering and pagination"""
        try:
            query = self.supabase.table(self.table_name).select("*")

            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            # Apply ordering
            if order_by:
                query = query.order(order_by, desc=not ascending)

            # Apply pagination
            query = query.limit(limit).offset(offset)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing records from {self.table_name}: {str(e)}")
            raise

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        try:
            query = self.supabase.table(self.table_name).select("id", count="exact")

            # Apply filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = query.execute()
            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting records in {self.table_name}: {str(e)}")
            raise
