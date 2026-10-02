import asyncio

from src.services.job_worker import redis_worker_loop


if __name__ == "__main__":
    asyncio.run(redis_worker_loop())
