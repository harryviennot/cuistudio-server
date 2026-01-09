"""
Rate limiting middleware using in-memory storage.

For production with multiple workers, consider using Redis backend
to share rate limit state across processes.
"""
import time
import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with separate limits for general requests
    and extraction endpoints.

    Uses a sliding window algorithm to track request counts per client.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        extraction_per_minute: int = 10
    ):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: General rate limit for all requests
            extraction_per_minute: Stricter limit for extraction endpoints
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.extraction_per_minute = extraction_per_minute
        self._request_counts: Dict[str, List[float]] = defaultdict(list)
        self._extraction_counts: Dict[str, List[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier from auth token or IP address.

        Prefers user-specific identification via auth token hash,
        falls back to IP address for unauthenticated requests.
        """
        # Prefer user ID from auth if available
        auth_header = request.headers.get("authorization", "")
        if auth_header:
            # Use hash of token to identify user without storing token
            return f"auth:{hash(auth_header)}"

        # Fallback to IP address
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Get first IP in chain (original client)
            return f"ip:{forwarded.split(',')[0].strip()}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    def _is_rate_limited(
        self,
        counts: List[float],
        limit: int,
        window: int = 60
    ) -> bool:
        """
        Check if client has exceeded rate limit using sliding window.

        Args:
            counts: List of request timestamps for this client
            limit: Maximum requests allowed in window
            window: Time window in seconds

        Returns:
            True if rate limit exceeded, False otherwise
        """
        now = time.time()
        # Remove old entries outside the time window
        counts[:] = [t for t in counts if now - t < window]

        if len(counts) >= limit:
            return True

        counts.append(now)
        return False

    def _get_retry_after(self, counts: List[float], window: int = 60) -> int:
        """Calculate seconds until rate limit resets."""
        if not counts:
            return 0
        oldest = min(counts)
        return max(1, int(window - (time.time() - oldest)))

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        client_id = self._get_client_id(request)
        path = request.url.path

        # Skip rate limiting for health check
        if path == "/health":
            return await call_next(request)

        # Stricter limit for extraction endpoints (POST only)
        if "/extraction/" in path and request.method == "POST":
            if self._is_rate_limited(
                self._extraction_counts[client_id],
                self.extraction_per_minute
            ):
                retry_after = self._get_retry_after(
                    self._extraction_counts[client_id]
                )
                logger.warning(
                    f"Extraction rate limit exceeded for {client_id}, "
                    f"retry after {retry_after}s"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Extraction rate limit exceeded. Please wait before trying again."},
                    headers={"Retry-After": str(retry_after)}
                )

        # General rate limit for all requests
        if self._is_rate_limited(
            self._request_counts[client_id],
            self.requests_per_minute
        ):
            retry_after = self._get_retry_after(self._request_counts[client_id])
            logger.warning(
                f"Rate limit exceeded for {client_id}, retry after {retry_after}s"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={"Retry-After": str(retry_after)}
            )

        return await call_next(request)
