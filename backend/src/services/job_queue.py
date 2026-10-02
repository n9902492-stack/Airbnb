import json
from typing import Any

from src.core.config import settings


class JobQueue:
    @staticmethod
    async def enqueue(name: str, payload: dict[str, Any]) -> bool:
        if not settings.redis_url:
            return False

        from redis.asyncio import Redis

        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            await redis.lpush(
                settings.redis_job_queue,
                json.dumps({"name": name, "payload": payload}),
            )
            return True
        finally:
            await redis.aclose()
