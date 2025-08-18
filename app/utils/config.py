
import os
import redis
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

    # JWT - FIXED NAMING CONSISTENCY
    JWT_SECRET: str = "supersecretkey"
    SECRET_KEY: str = "supersecretkey"  # alias for consistency
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = "HS256"  # alias for consistency
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # alias
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_EXPIRE_SECONDS: int = 86400  # 24 hours

    # Cache TTL settings (in seconds)
    COURSE_CACHE_TTL: int = 300  # 5 minutes
    COURSES_LIST_CACHE_TTL: int = 120  # 2 minutes
    USER_PROGRESS_CACHE_TTL: int = 600  # 10 minutes
    USER_DASHBOARD_CACHE_TTL: int = 300  # 5 minutes
    ANALYTICS_COURSE_TTL: int = 900  # 15 minutes
    ANALYTICS_PLATFORM_TTL: int = 3600  # 1 hour
    POPULAR_COURSES_TTL: int = 3600  # 1 hour
    USER_RECOMMENDATIONS_TTL: int = 21600  # 6 hours

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Test Redis availability safely
def test_redis_connection():
    """Test Redis connection without blocking startup"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2)
        redis_client.ping()
        redis_client.close()
        return True
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        return False


# Set Redis availability
settings.REDIS_AVAILABLE = test_redis_connection()

if settings.REDIS_AVAILABLE:
    print("✅ Redis is available and connected")
else:
    print("⚠️ Redis not available - some features will be limited")
    print("💡 Make sure Redis is running: redis-server")

# Debug configuration
if __name__ == "__main__":
    print("=== Configuration Debug ===")
    print(f"MONGO_URI: {settings.MONGO_URI}")
    print(f"REDIS_URL: {settings.REDIS_URL}")
    print(f"JWT_SECRET: {'***' if settings.JWT_SECRET else 'NOT SET'}")
    print(f"REDIS_AVAILABLE: {settings.REDIS_AVAILABLE}")





#
# import os
# from pydantic_settings import BaseSettings
# from dotenv import load_dotenv
#
# # Load .env file explicitly
# load_dotenv()
#
#
# class Settings(BaseSettings):
#     # MongoDB
#     MONGO_URI: str = "mongodb://localhost:27017"
#     MONGO_DB: str = "ELearningAPI"
#
#     # Redis
#     REDIS_HOST: str = "localhost"
#     REDIS_PORT: int = 6379
#     REDIS_DB: int = 0
#     REDIS_URL: str = "redis://localhost:6379/0"
#
#     # JWT
#     JWT_SECRET: str = "supersecretkey"
#     JWT_ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
#     REFRESH_TOKEN_EXPIRE_DAYS: int = 7
#     JWT_ACCESS_EXPIRE_MINUTES: int = 30
#
#     JWT_SECRET_KEY: str = "your_secret_key_here"  # Change to a secure value
#     JWT_ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
#
#     # Cache TTL settings (in seconds)
#     COURSE_CACHE_TTL: int = 300  # 5 minutes
#     COURSES_LIST_CACHE_TTL: int = 120  # 2 minutes
#     USER_PROGRESS_CACHE_TTL: int = 600  # 10 minutes
#     USER_DASHBOARD_CACHE_TTL: int = 300  # 5 minutes
#     ANALYTICS_COURSE_TTL: int = 900  # 15 minutes
#     ANALYTICS_PLATFORM_TTL: int = 3600  # 1 hour
#     POPULAR_COURSES_TTL: int = 3600  # 1 hour
#     USER_RECOMMENDATIONS_TTL: int = 21600  # 6 hours
#
#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"
#
#
# # Create settings instance
# settings = Settings()
#
# # Debug print
# if __name__ == "__main__":
#     print("=== Configuration Debug ===")
#     print(f"MONGO_URI: {settings.MONGO_URI}")
#     print(f"REDIS_URL: {settings.REDIS_URL}")
#     print(f"JWT_SECRET: {'***' if settings.JWT_SECRET else 'NOT SET'}")
#     print(f"Environment file exists: {os.path.exists('.env')}")
#
#     # Print environment variables
#     print("\n=== Environment Variables ===")
#     for key in ['MONGO_URI', 'REDIS_URL', 'JWT_SECRET']:
#         print(f"{key}: {os.getenv(key, 'NOT SET')}")