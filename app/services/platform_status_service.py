"""
Platform Status Service
Tracks platform extraction requirements and failure patterns for dynamic client-download detection.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from supabase import Client

logger = logging.getLogger(__name__)


class PlatformStatusService:
    """
    Service for tracking platform extraction status and requirements.

    Features:
    - Track which platforms require client-side download
    - Dynamically update based on failure patterns
    - Auto-mark platforms as needing client download after threshold failures
    """

    # Failure threshold before marking platform as requiring client download
    FAILURE_THRESHOLD = 3

    # Cache TTL in seconds (10 minutes)
    CACHE_TTL_SECONDS = 600

    def __init__(self, supabase: Client):
        """
        Initialize PlatformStatusService.

        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamp: Optional[datetime] = None

    def _normalize_domain(self, domain: str) -> str:
        """
        Normalize a domain for consistent lookups.

        Args:
            domain: Domain to normalize

        Returns:
            Normalized domain (lowercase, no www prefix)
        """
        return domain.lower().replace("www.", "").strip()

    async def requires_client_download(self, domain: str) -> bool:
        """
        Check if a platform requires client-side download.

        Args:
            domain: Platform domain (e.g., 'instagram.com')

        Returns:
            True if client download is required
        """
        domain = self._normalize_domain(domain)

        # Check cache first
        if domain in self._cache:
            return self._cache[domain].get("requires_client_download", False)

        # Query database
        status = await self._get_status(domain)
        if status:
            self._cache[domain] = status
            return status.get("requires_client_download", False)

        return False

    async def record_failure(
        self,
        domain: str,
        failure_reason: str
    ) -> bool:
        """
        Record an extraction failure for a platform.

        If failures exceed threshold, automatically marks the platform
        as requiring client-side download.

        Args:
            domain: Platform domain
            failure_reason: Reason for failure (auth_required, rate_limited, blocked, etc.)

        Returns:
            True if platform was marked as requiring client download
        """
        domain = self._normalize_domain(domain)

        try:
            status = await self._get_status(domain)
            now = datetime.now(timezone.utc)

            if status:
                # Update existing record
                new_count = status.get("failure_count", 0) + 1
                should_require_client = new_count >= self.FAILURE_THRESHOLD

                update_data = {
                    "failure_count": new_count,
                    "last_failure_at": now.isoformat(),
                    "failure_reason": failure_reason,
                    "updated_at": now.isoformat()
                }

                # Only update requires_client_download if crossing threshold
                if should_require_client and not status.get("requires_client_download"):
                    update_data["requires_client_download"] = True
                    logger.info(
                        f"Platform {domain} now requires client download "
                        f"after {new_count} failures (reason: {failure_reason})"
                    )

                await asyncio.to_thread(
                    lambda: self.supabase.table("platform_status")
                        .update(update_data)
                        .eq("platform_domain", domain)
                        .execute()
                )

                # Update cache
                self._cache[domain] = {
                    **status,
                    **update_data
                }

                return should_require_client and not status.get("requires_client_download")

            else:
                # Create new record
                insert_data = {
                    "platform_domain": domain,
                    "failure_count": 1,
                    "last_failure_at": now.isoformat(),
                    "failure_reason": failure_reason,
                    "requires_client_download": False
                }

                await asyncio.to_thread(
                    lambda: self.supabase.table("platform_status")
                        .insert(insert_data)
                        .execute()
                )

                self._cache[domain] = insert_data
                logger.debug(f"Created platform status for {domain} (first failure)")

                return False

        except Exception as e:
            logger.error(f"Failed to record platform failure for {domain}: {e}")
            return False

    async def record_success(self, domain: str) -> None:
        """
        Record a successful extraction. Resets failure count.

        Args:
            domain: Platform domain
        """
        domain = self._normalize_domain(domain)

        try:
            now = datetime.now(timezone.utc)

            # Upsert: create if not exists, update if exists
            upsert_data = {
                "platform_domain": domain,
                "failure_count": 0,
                "last_success_at": now.isoformat(),
                "updated_at": now.isoformat()
            }

            await asyncio.to_thread(
                lambda: self.supabase.table("platform_status")
                    .upsert(upsert_data, on_conflict="platform_domain")
                    .execute()
            )

            # Update cache
            if domain in self._cache:
                self._cache[domain]["failure_count"] = 0
                self._cache[domain]["last_success_at"] = now.isoformat()

            logger.debug(f"Recorded success for {domain}")

        except Exception as e:
            logger.error(f"Failed to record platform success for {domain}: {e}")

    async def get_all_statuses(self) -> list:
        """
        Get all platform statuses.

        Returns:
            List of platform status records
        """
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("platform_status")
                    .select("*")
                    .order("platform_domain")
                    .execute()
            )
            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get all platform statuses: {e}")
            return []

    async def get_client_required_platforms(self) -> list:
        """
        Get list of platforms that require client-side download.

        Returns:
            List of platform domains
        """
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("platform_status")
                    .select("platform_domain")
                    .eq("requires_client_download", True)
                    .execute()
            )
            return [r["platform_domain"] for r in (result.data or [])]

        except Exception as e:
            logger.error(f"Failed to get client-required platforms: {e}")
            return []

    async def reset_platform(self, domain: str) -> bool:
        """
        Reset a platform's failure count and client requirement.
        Useful for manual intervention.

        Args:
            domain: Platform domain to reset

        Returns:
            True if reset was successful
        """
        domain = self._normalize_domain(domain)

        try:
            now = datetime.now(timezone.utc)

            await asyncio.to_thread(
                lambda: self.supabase.table("platform_status")
                    .update({
                        "failure_count": 0,
                        "requires_client_download": False,
                        "failure_reason": None,
                        "updated_at": now.isoformat()
                    })
                    .eq("platform_domain", domain)
                    .execute()
            )

            # Clear from cache
            if domain in self._cache:
                del self._cache[domain]

            logger.info(f"Reset platform status for {domain}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset platform {domain}: {e}")
            return False

    async def _get_status(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get platform status from database.

        Args:
            domain: Platform domain

        Returns:
            Status dict if found, None otherwise
        """
        try:
            result = await asyncio.to_thread(
                lambda: self.supabase.table("platform_status")
                    .select("*")
                    .eq("platform_domain", domain)
                    .maybe_single()
                    .execute()
            )
            return result.data

        except Exception as e:
            logger.error(f"Failed to get platform status for {domain}: {e}")
            return None

    def invalidate_cache(self) -> None:
        """
        Manually invalidate the cache.
        """
        self._cache = {}
        self._cache_timestamp = None
        logger.info("Platform status cache invalidated")

    @staticmethod
    def extract_domain_from_url(url: str) -> str:
        """
        Extract the domain from a URL.

        Args:
            url: Full URL

        Returns:
            Domain (e.g., 'instagram.com')
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain.replace("www.", "")
        except Exception:
            return ""
