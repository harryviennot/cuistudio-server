"""
Feature Flag Service
Provides feature flag management for gradual rollout and A/B testing of new features.
"""
import asyncio
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from supabase import Client

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """
    Service for managing feature flags with support for:
    - Global on/off toggles
    - Percentage-based rollout
    - User-specific flag evaluation
    - In-memory caching with TTL
    """

    # Cache TTL in seconds (5 minutes)
    CACHE_TTL_SECONDS = 300

    def __init__(self, supabase: Client):
        """
        Initialize FeatureFlagService.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamp: Optional[datetime] = None

    async def is_enabled(self, flag_name: str) -> bool:
        """
        Check if a feature flag is globally enabled.

        Args:
            flag_name: Name of the feature flag

        Returns:
            True if the flag is enabled, False otherwise
        """
        flag = await self._get_flag(flag_name)
        if not flag:
            logger.debug(f"Feature flag '{flag_name}' not found, defaulting to False")
            return False

        return flag.get("enabled", False)

    async def is_enabled_for_user(self, flag_name: str, user_id: str) -> bool:
        """
        Check if a feature flag is enabled for a specific user.

        Uses percentage-based rollout: hashes the user_id and flag_name
        to deterministically assign the user to the rollout group.

        Args:
            flag_name: Name of the feature flag
            user_id: UUID of the user

        Returns:
            True if the flag is enabled for this user, False otherwise
        """
        flag = await self._get_flag(flag_name)
        if not flag:
            logger.debug(f"Feature flag '{flag_name}' not found, defaulting to False")
            return False

        # If globally enabled, return True
        if flag.get("enabled", False):
            return True

        # Check percentage-based rollout
        rollout_percentage = flag.get("rollout_percentage", 0)
        if rollout_percentage <= 0:
            return False

        if rollout_percentage >= 100:
            return True

        # Deterministic hash-based rollout
        user_hash = self._hash_user_for_rollout(flag_name, user_id)
        return user_hash < rollout_percentage

    async def get_all_flags(self) -> Dict[str, bool]:
        """
        Get the current state of all feature flags.

        Returns:
            Dict mapping flag names to their enabled state
        """
        flags = await self._get_all_flags()
        return {flag["flag_name"]: flag.get("enabled", False) for flag in flags}

    async def _get_flag(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific feature flag from cache or database.

        Args:
            flag_name: Name of the feature flag

        Returns:
            Flag dict if found, None otherwise
        """
        await self._ensure_cache_fresh()

        if flag_name in self._cache:
            return self._cache[flag_name]

        # Not in cache, try to fetch from database
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("feature_flags")
                    .select("*")
                    .eq("flag_name", flag_name)
                    .single()
                    .execute()
            )
            if result.data:
                self._cache[flag_name] = result.data
                return result.data
        except Exception as e:
            logger.error(f"Failed to fetch feature flag '{flag_name}': {e}")

        return None

    async def _get_all_flags(self) -> list:
        """
        Get all feature flags from cache or database.

        Returns:
            List of flag dicts
        """
        await self._ensure_cache_fresh()
        return list(self._cache.values())

    async def _ensure_cache_fresh(self) -> None:
        """
        Ensure the cache is fresh, refreshing if TTL has expired.
        """
        now = datetime.now(timezone.utc)

        if self._cache_timestamp is None:
            await self._refresh_cache()
            return

        cache_age = now - self._cache_timestamp
        if cache_age > timedelta(seconds=self.CACHE_TTL_SECONDS):
            await self._refresh_cache()

    async def _refresh_cache(self) -> None:
        """
        Refresh the entire cache from the database.
        """
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("feature_flags")
                    .select("*")
                    .execute()
            )

            if result.data:
                self._cache = {flag["flag_name"]: flag for flag in result.data}
                self._cache_timestamp = datetime.now(timezone.utc)
                logger.debug(f"Feature flags cache refreshed: {len(self._cache)} flags")
            else:
                self._cache = {}
                self._cache_timestamp = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to refresh feature flags cache: {e}")
            # Keep stale cache rather than clearing it
            if self._cache_timestamp is None:
                self._cache = {}
                self._cache_timestamp = datetime.now(timezone.utc)

    def _hash_user_for_rollout(self, flag_name: str, user_id: str) -> int:
        """
        Generate a deterministic hash (0-99) for a user and flag combination.

        This ensures the same user always gets the same rollout decision
        for a given flag, but different flags may have different decisions.

        Args:
            flag_name: Name of the feature flag
            user_id: UUID of the user

        Returns:
            Integer from 0-99 representing the user's rollout bucket
        """
        combined = f"{flag_name}:{user_id}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        # Use first 4 bytes as an integer, then mod 100
        hash_int = int.from_bytes(hash_bytes[:4], byteorder="big")
        return hash_int % 100

    def invalidate_cache(self) -> None:
        """
        Manually invalidate the cache.
        Useful after updating flags via admin interface.
        """
        self._cache = {}
        self._cache_timestamp = None
        logger.info("Feature flags cache invalidated")


# Singleton instance for convenience
_instance: Optional[FeatureFlagService] = None


def get_feature_flag_service(supabase: Client) -> FeatureFlagService:
    """
    Get or create the FeatureFlagService singleton.

    Args:
        supabase: Supabase client instance

    Returns:
        FeatureFlagService instance
    """
    global _instance
    if _instance is None:
        _instance = FeatureFlagService(supabase)
    return _instance
