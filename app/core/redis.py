import redis

redis_client = redis.Redis(
    host="localhost",
    port=5678,
    db=0,
    decode_responses=True
)

#docker run -d --name redis -p 5678  redis:6379 redis