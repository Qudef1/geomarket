import json
import logging
from typing import Any, Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class Cache(Protocol):
    async def get_json(self, key: str) -> Any | None: ...
    async def set_json(self, key: str, value: Any, ttl: int) -> None: ...


class RedisCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def get_json(self, key: str) -> Any | None:
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except (RedisError, json.JSONDecodeError):
            logger.warning("cache_read_failed", exc_info=True)
            return None

    async def set_json(self, key: str, value: Any, ttl: int) -> None:
        try:
            await self.redis.set(key, json.dumps(value), ex=ttl)
        except RedisError:
            logger.warning("cache_write_failed", exc_info=True)


class MemoryCache:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    async def get_json(self, key: str) -> Any | None:
        return self.values.get(key)

    async def set_json(self, key: str, value: Any, ttl: int) -> None:
        self.values[key] = value
