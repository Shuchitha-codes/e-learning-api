"""
Cache management endpoints for E-Learning API

Endpoints:
- GET /cache/stats : Show Redis stats (admin only)
- DELETE /cache/flush : Clear Redis cache (admin only)
"""

from app.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_redis  # instead of app.dependencies

router = APIRouter()


# -----------------------
# Cache Stats
# -----------------------
@router.get("/stats")
async def cache_stats(redis=Depends(get_redis), user=Depends(get_current_user)):
    """
    Show Redis statistics.
    Only accessible to admin users.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can see cache stats")

    info = redis.info()
    dbsize = redis.dbsize()

    return {
        "connected": True,
        "dbsize": dbsize,
        "used_memory_human": info.get("memory", {}).get("used_memory_human")
    }


# -----------------------
# Flush Cache
# -----------------------
@router.delete("/flush")
async def flush_cache(redis=Depends(get_redis), user=Depends(get_current_user)):
    """
    Clear all keys in Redis database.
    Only accessible to admin users.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can flush cache")

    redis.flushdb()
    return {"status": "Cache cleared"}
