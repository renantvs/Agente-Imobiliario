import redis
from app.core.config import settings

redis_client: redis.Redis = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)

__all__ = ["redis_client"]
