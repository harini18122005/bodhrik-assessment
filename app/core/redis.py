import redis.asyncio as redis

from app.core.config import settings

# Create a connection pool for Redis to reuse connections efficiently
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis_client() -> redis.Redis:
    """Retrieve an active Redis client using the connection pool."""
    return redis.Redis(connection_pool=redis_pool)


class RedisQueue:
    """Asynchronous Redis-backed FIFO queue utilizing LPUSH and BRPOP."""

    def __init__(self, name: str):
        self.name = name

    async def enqueue(self, value: str) -> None:
        """Add an element to the tail of the queue (left-push)."""
        client = await get_redis_client()
        await client.lpush(self.name, value)

    async def dequeue(self, timeout: int = 0) -> str | None:
        """Remove and return an element from the head of the queue (blocking right-pop).

        Blocks until an item is available if timeout is set.
        """
        client = await get_redis_client()
        result = await client.brpop(self.name, timeout=timeout)
        if result:
            return result[1]
        return None
