
from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.config import settings
import redis.asyncio as aioredis# --- Redis setup ---
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]


