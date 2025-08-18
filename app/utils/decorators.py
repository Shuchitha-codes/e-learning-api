
import json
from functools import wraps
from jose import jwt, JWTError
from fastapi import HTTPException, status
import redis.asyncio as aioredis
from app.utils.config import settings

# ------------------- JWT Access Token Verification -------------------
async def verify_access_token(token: str, redis_client: aioredis.Redis):

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

        # check if token is blacklisted
        is_blacklisted = await redis_client.get(f"blacklisted_tokens:{jti}")
        if is_blacklisted:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

        return payload

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


# ------------------- Redis Cache Decorator -------------------
def redis_cache(redis_client: aioredis.Redis, key: str, ttl: int):

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cached_data = await redis_client.get(key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    pass  # fallback to calling function

            result = await func(*args, **kwargs)
            await redis_client.set(key, json.dumps(result), ex=ttl)
            return result

        return wrapper
    return decorator


# ------------------- Cache Invalidation -------------------
async def invalidate_cache(redis_client: aioredis.Redis, key: str):

    await redis_client.delete(key)
