import redis.asyncio as redis
from app.core.config import settings

pool_blacklist = redis.ConnectionPool.from_url(
    url=settings.BACKLIST_REDIS_URL,
    decode_responses=True
)

pool_jobs = redis.ConnectionPool.from_url(
    url=settings.JOBS_REDIS_URL,
    decode_responses=True
)


redis_client = redis.Redis(connection_pool=pool_blacklist)
redis_jobs = redis.Redis(connection_pool=pool_jobs)

QUEUE_KEY = "system:queue:work" #เก็บงานที่พร้อมทำ
