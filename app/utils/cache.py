#
# import json
# from functools import wraps
#
#

# app/utils/cache.py
import json
from functools import wraps

def redis_cache(redis_client, key: str, ttl: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cached = await redis_client.get(key)
            if cached:
                return json.loads(cached)
            result = await func(*args, **kwargs)
            await redis_client.set(key, json.dumps(result), ex=ttl)
            return result
        return wrapper
    return decorator

async def invalidate_cache(redis_client, key: str):
    async for k in redis_client.scan_iter(key):
        await redis_client.delete(k)

# ✅ Add direct helpers so you can call cache.get / cache.set
async def get(redis_client, key: str):
    data = await redis_client.get(key)
    return json.loads(data) if data else None

async def set(redis_client, key: str, value: dict, ttl: int = 3600):
    await redis_client.set(key, json.dumps(value), ex=ttl)
