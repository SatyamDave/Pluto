import time
import hashlib
from typing import Optional
import redis

from ..core.config import settings

_pool = None

def _get_redis():
    global _pool
    if _pool is None:
        _pool = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _pool


def _bucket_key(scope: str, identifier: str) -> str:
    h = hashlib.sha256(identifier.encode()).hexdigest()[:16]
    return f"rl:{scope}:{h}"


def token_bucket_allow(scope: str, identifier: str, capacity: int, refill_rate_per_sec: float) -> bool:
    r = _get_redis()
    key = _bucket_key(scope, identifier)
    now = time.time()
    bucket = r.hmget(key, "tokens", "last")
    tokens = float(bucket[0]) if bucket[0] else capacity
    last = float(bucket[1]) if bucket[1] else now
    # refill
    elapsed = max(0.0, now - last)
    tokens = min(capacity, tokens + elapsed * refill_rate_per_sec)
    allowed = tokens >= 1.0
    if allowed:
        tokens -= 1.0
    pipe = r.pipeline()
    pipe.hset(key, mapping={"tokens": tokens, "last": now})
    pipe.expire(key, int(max(2 * capacity / max(1e-6, refill_rate_per_sec), 60)))
    pipe.execute()
    return allowed


def per_ip_allow(ip: str, capacity: int = 60, refill_rate_per_sec: float = 0.5) -> bool:
    return token_bucket_allow("ip", ip, capacity, refill_rate_per_sec)


def per_slug_allow(slug: str, capacity: int = 120, refill_rate_per_sec: float = 1.0) -> bool:
    return token_bucket_allow("slug", slug, capacity, refill_rate_per_sec)
