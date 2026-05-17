import redis.asyncio as aioredis
import logging
from app.core.config import REDIS_URL

logger = logging.getLogger("bikeride.redis")
redis_client: aioredis.Redis = None

async def get_redis() -> aioredis.Redis:
    return redis_client

async def connect_redis():
    global redis_client
    redis_client = aioredis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    logger.info("Redis connected successfully")

async def disconnect_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis disconnected")