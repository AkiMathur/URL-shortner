import json
import logging
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # 1 hour


def _make_key(shorturl: str) -> str:
    return f"link:{shorturl}"


def get_cached_link(redis: Redis, shorturl: str) -> dict | None:
    """Retrieve link metadata from Redis. Returns None on cache miss or Redis failure."""
    try:
        cached = redis.get(_make_key(shorturl))
        return json.loads(cached) if cached else None
    except RedisError as e:
        logger.warning(f"Redis get failed for '{shorturl}': {e}")
        return None


def set_cached_link(redis: Redis, shorturl: str, data: dict, ttl: int = CACHE_TTL) -> None:
    """Cache link metadata in Redis with a TTL. Fails gracefully if Redis is down."""
    try:
        redis.set(_make_key(shorturl), json.dumps(data), ex=ttl)
    except RedisError as e:
        logger.warning(f"Redis set failed for '{shorturl}': {e}")


def invalidate_link(redis: Redis, shorturl: str) -> None:
    """Evict link from Redis on update/delete. Fails gracefully if Redis is down."""
    try:
        redis.delete(_make_key(shorturl))
    except RedisError as e:
        logger.warning(f"Redis eviction failed for '{shorturl}': {e}")
