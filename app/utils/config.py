import os
import redis.asyncio as aioredis   # async Redis
import motor.motor_asyncio         # async Mongo
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()


class Settings(BaseSettings):
    # App
    APP_NAME: str = "E-Learning API"

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "ELearningAPI"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_AVAILABLE: bool = False

    # JWT
    JWT_SECRET: str = "supersecretkey"
    SECRET_KEY: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_EXPIRE_SECONDS: int = 86400  # 24h

    # Cache TTL settings
    COURSE_CACHE_TTL: int = 300
    COURSES_LIST_CACHE_TTL: int = 120
    USER_PROGRESS_CACHE_TTL: int = 600
    USER_DASHBOARD_CACHE_TTL: int = 300
    ANALYTICS_COURSE_TTL: int = 900
    ANALYTICS_PLATFORM_TTL: int = 3600
    POPULAR_COURSES_TTL: int = 3600
    USER_RECOMMENDATIONS_TTL: int = 21600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# ✅ MongoDB client
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
db = mongo_client[settings.MONGO_DB]

# ✅ Redis client
redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


# Test Redis availability safely
def test_redis_connection():
    """Test Redis connection without blocking startup"""
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(redis.ping())
        return True
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        return False


settings.REDIS_AVAILABLE = test_redis_connection()

if settings.REDIS_AVAILABLE:
    print("✅ Redis is available and connected")
else:
    print("⚠️ Redis not available - some features will be limited")
    print("💡 Make sure Redis is running: redis-server")
