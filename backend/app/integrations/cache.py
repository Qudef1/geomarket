import json
from typing import Any, Protocol

from redis.asyncio import Redis


class Cache(Protocol):
    async def get_json(self, key: str) -> Any | None: ...
    async def set_json(self, key: str, value: Any, ttl: int) -> None: ...


class RedisCache:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def get_json(self, key: str) -> Any | None:
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set_json(self, key: str, value: Any, ttl: int) -> None:
        await self.redis.set(key, json.dumps(value), ex=ttl)


class MemoryCache:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    async def get_json(self, key: str) -> Any | None:
        return self.values.get(key)

    async def set_json(self, key: str, value: Any, ttl: int) -> None:
        self.values[key] = value
