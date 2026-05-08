import json
import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

def _cache_key(url: str) -> str:
    return f"scan:{url}"

async def get_cached_result(url: str) -> dict | None:
    r = await get_redis()
    raw = await r.get(_cache_key(url))
    if raw:
        return json.loads(raw)
    return None

async def set_cached_result(url: str, data: dict) -> None:
    r = await get_redis()
    await r.setex(
        _cache_key(url),
        settings.CACHE_TTL_SECONDS,
        json.dumps(data, default=str),
    )

async def invalidate_cache(url: str) -> None:
    r = await get_redis()
    await r.delete(_cache_key(url))

async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
