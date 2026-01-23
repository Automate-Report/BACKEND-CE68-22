import redis

redis_client = redis.Redis(
    host="10.20.20.108",
    port=5678,
    db=0,
    decode_responses=True
)
redis_worker = redis.Redis(
    host="10.20.20.108",
    port=5678,
    db=1,
    decode_responses=True
)

SECHEDULE_KEY = "system:schedule" #เก็บงานรอเวลา
QUEUE_KEY = "system:queue" #เก็บงานที่พร้อมทำ



#docker run -d --name redis -p 5678  redis:6379 redis