"""
Event broadcasting system for real-time updates
Supports both Redis pub/sub (multi-instance) and in-memory (single-instance)
"""
import json
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """
    Event broadcaster for extraction job updates.
    Supports Redis pub/sub for multi-instance deployments and in-memory for single-instance.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize event broadcaster.

        Args:
            redis_url: Redis connection URL. If None, uses in-memory broadcasting.
        """
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None

        # In-memory event channels (fallback for single-instance deployments)
        self._memory_channels: Dict[str, asyncio.Queue] = {}

        logger.info(f"EventBroadcaster initialized with {'Redis' if redis_url else 'in-memory'} backend")

    async def connect(self):
        """Connect to Redis if configured"""
        if self.redis_url:
            try:
                import redis.asyncio as redis
                self.redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Connected to Redis for event broadcasting")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, falling back to in-memory: {e}")
                self.redis_client = None

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    def _get_channel_key(self, job_id: str) -> str:
        """Get Redis channel key for a job"""
        return f"extraction:job:{job_id}"

    async def publish(self, job_id: str, event_data: Dict[str, Any]):
        """
        Publish an event for a job.

        Args:
            job_id: The extraction job ID
            event_data: Event data to publish (will be JSON serialized)
        """
        try:
            event_json = json.dumps(event_data)
            channel_key = self._get_channel_key(job_id)

            if self.redis_client:
                # Redis pub/sub
                await self.redis_client.publish(channel_key, event_json)
                logger.debug(f"Published event to Redis channel {channel_key}: {event_data}")
            else:
                # In-memory broadcasting
                if channel_key in self._memory_channels:
                    await self._memory_channels[channel_key].put(event_data)
                    logger.debug(f"Published event to memory channel {channel_key}: {event_data}")
        except Exception as e:
            logger.error(f"Failed to publish event for job {job_id}: {e}")

    @asynccontextmanager
    async def subscribe(self, job_id: str):
        """
        Subscribe to events for a job.

        Args:
            job_id: The extraction job ID

        Yields:
            Async iterator of event dictionaries
        """
        channel_key = self._get_channel_key(job_id)

        if self.redis_client:
            # Redis pub/sub subscription
            pubsub = self.redis_client.pubsub()
            try:
                await pubsub.subscribe(channel_key)
                logger.info(f"Subscribed to Redis channel: {channel_key}")

                async def event_generator():
                    """Generate events from Redis pub/sub"""
                    try:
                        async for message in pubsub.listen():
                            if message["type"] == "message":
                                try:
                                    event_data = json.loads(message["data"])
                                    yield event_data
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to decode event: {e}")
                    except asyncio.CancelledError:
                        logger.info(f"Subscription cancelled for {channel_key}")
                        raise
                    except Exception as e:
                        logger.error(f"Error in event generator: {e}")

                yield event_generator()
            finally:
                await pubsub.unsubscribe(channel_key)
                await pubsub.close()
                logger.info(f"Unsubscribed from Redis channel: {channel_key}")
        else:
            # In-memory subscription
            queue = asyncio.Queue()
            self._memory_channels[channel_key] = queue

            try:
                logger.info(f"Subscribed to memory channel: {channel_key}")

                async def event_generator():
                    """Generate events from in-memory queue"""
                    try:
                        while True:
                            event_data = await queue.get()
                            yield event_data
                    except asyncio.CancelledError:
                        logger.info(f"Subscription cancelled for {channel_key}")
                        raise
                    except Exception as e:
                        logger.error(f"Error in event generator: {e}")

                yield event_generator()
            finally:
                # Clean up memory channel
                if channel_key in self._memory_channels:
                    del self._memory_channels[channel_key]
                logger.info(f"Unsubscribed from memory channel: {channel_key}")


# Global broadcaster instance
_broadcaster: Optional[EventBroadcaster] = None


def get_event_broadcaster() -> EventBroadcaster:
    """Get the global event broadcaster instance"""
    global _broadcaster
    if _broadcaster is None:
        # Try to get Redis URL from environment
        import os
        redis_url = os.getenv("REDIS_URL")
        _broadcaster = EventBroadcaster(redis_url)
    return _broadcaster


async def init_event_broadcaster():
    """Initialize and connect the event broadcaster (call on app startup)"""
    broadcaster = get_event_broadcaster()
    await broadcaster.connect()


async def shutdown_event_broadcaster():
    """Shutdown the event broadcaster (call on app shutdown)"""
    global _broadcaster
    if _broadcaster:
        await _broadcaster.disconnect()
        _broadcaster = None
