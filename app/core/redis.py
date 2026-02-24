import redis.asyncio as redis

pool_blacklist = redis.ConnectionPool.from_url(
    url="redis://10.60.1.214:5678/0",
    # url="redis://localhost:5678/0",
    decode_responses=True
)

pool_jobs = redis.ConnectionPool.from_url(
    url="redis://10.60.1.214:5678/1",
    # url="redis://localhost:5678/1",
    decode_responses=True
)


# redis_client = redis.Redis(
#     host="10.20.20.108",
#     port=5678,
#     db=0,
#     decode_responses=True
# )
# redis_worker = redis.Redis(
#     host="10.20.20.108",
#     port=5678,
#     db=1,
#     decode_responses=True
# )

redis_client = redis.Redis(connection_pool=pool_blacklist)
redis_jobs = redis.Redis(connection_pool=pool_jobs)

QUEUE_KEY = "system:queue:work" #เก็บงานที่พร้อมทำ

#docker run -d --name redis -p 5678  redis:6379 redis