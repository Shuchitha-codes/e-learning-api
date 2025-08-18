# app/routes/progress.py


from app.dependencies import get_database
from app.services.progress_service import ProgressService
from pymongo.database import Database
import redis
# For example, auth.py
from fastapi import APIRouter, Depends
from app.dependencies import get_redis  # instead of app.dependencies

router = APIRouter()

@router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(user_id: str, course_id: str, lesson_id: str, time_spent: int, quiz_score: int, db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):

    service = ProgressService(db, redis_client)
    await service.update_lesson_progress(user_id, course_id, lesson_id, time_spent, quiz_score)
    return {"message": "Lesson progress updated"}

@router.get("/dashboard")
async def dashboard(user_id: str, db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):

    cache_key = f"user_dashboard:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return cached
    # Fetch progress and compute dashboard data
    progress_data = await db.progress.find({"user_id": user_id}).to_list(None)
    redis_client.set(cache_key, str(progress_data), ex=300)
    return progress_data

@router.get("/courses/{course_id}")
async def course_progress(user_id: str, course_id: str, db: Database = Depends(get_database), redis_client: redis.Redis = Depends(get_redis)):

    cache_key = f"progress:{user_id}:{course_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return cached
    progress = await db.progress.find_one({"user_id": user_id, "course_id": course_id})
    redis_client.set(cache_key, str(progress), ex=600)
    return progress
