from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient

from app.utils.config import settings  # ✅ keep settings source consistent

# Create MongoDB client
mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
db = mongo_client[settings.MONGO_DB]

async def get_database():

    return db


# Create Redis client (lazy connection)
redis_client: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:

    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            decode_responses=True  # ✅ returns str, don't .decode() later
        )
    return redis_client

async def ping_redis(redis_client: aioredis.Redis = Depends(get_redis)):

    try:
        pong = await redis_client.ping()
        if pong:
            return {"status": "success", "message": "Redis is running"}
        else:
            raise HTTPException(status_code=500, detail="Redis did not respond properly")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")

async def cache_user_session(user: dict, redis_client: aioredis.Redis):

    key = f"user_session:{user['username']}"
    await redis_client.setex(
        key,
        settings.SESSION_EXPIRE_SECONDS,
        str(user["_id"])
    )

# ============================================================
# ------------------ AUTH & SECURITY -------------------------
# ============================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify raw password against hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password securely."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta):
    """Create JWT access token with expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict):
    """Create JWT refresh token with expiry (days)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_database)):

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user




async def close_connections():
    """
    Gracefully close MongoDB + Redis connections.
    Should be called on FastAPI shutdown event.
    """
    global redis_client
    # Close MongoDB
    mongo_client.close()
    # Close Redis if connected
    if redis_client:
        await redis_client.close()
        redis_client = None
