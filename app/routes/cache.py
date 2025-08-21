"""
Cache management endpoints for E-Learning API

Endpoints:
- GET /cache/stats : Show Redis stats (admin only)
- DELETE /cache/flush : Clear Redis cache (admin only)
"""

from app.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_redis  # instead of app.dependencies
import redis.asyncio as redis

router = APIRouter()


# -----------------------

@router.get("/stats")
async def cache_stats(redis=Depends(get_redis), user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can see cache stats")

    info = await redis.info()
    dbsize = await redis.dbsize()

    return {
        "connected": True,
        "dbsize": dbsize,
        "used_memory_human": info.get("used_memory_human")
    }


@router.delete("/flush")
async def flush_cache(redis=Depends(get_redis), user=Depends(get_current_user)):
    """
    Clear all keys in Redis database.
    Only accessible to admin users.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can flush cache")

    await redis.flushdb()  # <-- important for async redis
    return {"status": "Cache cleared"}
