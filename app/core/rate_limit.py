from fastapi import HTTPException, Request
from redis.exceptions import RedisError


def rate_limit(limit: int, window: int, scope: str):
    """Allow `limit` requests per `window` seconds, per client IP, per scope."""

    def dependency(request: Request):
        ip = request.client.host if request.client else "unknown"
        key = f"rate:{scope}:{ip}"
        r = request.app.state.redis

        try:
            pipe = r.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            count, ttl = pipe.execute()

            # No expiry set yet (first hit, or a crash before expire ran)
            if ttl == -1:
                r.expire(key, window)
                ttl = window
        except RedisError:
            return  # fail open: Redis down should not take the API down

        if count > limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": str(max(ttl, 1))},
            )

    return dependency