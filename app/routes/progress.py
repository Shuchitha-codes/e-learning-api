# app/routes/progress.py
from bson import ObjectId
from app.utils import cache

from app.dependencies import get_database, get_redis, redis_client
from app.services.progress_service import ProgressService
from pymongo.database import Database
#import redis
import json
# For example, auth.py
from fastapi import APIRouter, Depends , Query, HTTPException, Path
import redis.asyncio as redis
from app.db import db,redis_client   # ✅ import db from app/db.py
from app.utils.config import settings


router = APIRouter()
# ---------- Lesson Completion ----------
@router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(
    lesson_id: str,
    user_id: str = Query(...),
    course_id: str = Query(...),
    time_spent: int = Query(0),
    quiz_score: int = Query(0),
    db: Database = Depends(get_database),
    redis_client: redis.Redis = Depends(get_redis)
):
    service = ProgressService(db, redis_client)
    await service.update_lesson_progress(user_id, course_id, lesson_id, time_spent, quiz_score)
    return {"message": "Lesson progress updated"}


# ---------- Dashboard (All Courses of a User) ----------

# Helper function to convert ObjectId to string
def serialize_progress(progress_list):
    serialized = []
    for doc in progress_list:
        doc_copy = dict(doc)  # make a copy to avoid modifying original
        for key, value in doc_copy.items():
            if isinstance(value, ObjectId):
                doc_copy[key] = str(value)
        serialized.append(doc_copy)
    return serialized


@router.get("/dashboard")
async def get_dashboard_data(user_id: str):
    cache_key = f"user:{user_id}:dashboard"

    # 1️⃣ Check Redis cache first
    cached_data = await cache.get(redis_client, cache_key)
    if cached_data:
        # Redis returns JSON string, convert back to dict
        return json.loads(cached_data)

    # 2️⃣ Fetch all progress documents for the given user_id
    user_progress = await db.progress.find({"user_id": user_id}).to_list(length=None)
    if not user_progress:
        return {"error": "No progress found for this user"}

    # 3️⃣ Serialize ObjectIds
    user_progress_serialized = serialize_progress(user_progress)
    result = {"progress": user_progress_serialized}

    # 4️⃣ Store in Redis for 15 minutes
    await cache.set(redis_client, cache_key, json.dumps(result), ttl=900)

    # 5️⃣ Return the result
    return result


# --------------------------------------------------
# GET /progress/courses/{course_id}
# Cached user progress for one course
# --------------------------------------------------
# Helper to serialize ObjectId
# Helper to serialize ObjectId
def serialize_doc(doc):
    doc_copy = dict(doc)
    for k, v in doc_copy.items():
        from bson import ObjectId
        if isinstance(v, ObjectId):
            doc_copy[k] = str(v)
    return doc_copy


# Helper to serialize ObjectId
def serialize_doc(doc):
    doc_copy = dict(doc)
    for k, v in doc_copy.items():
        if isinstance(v, ObjectId):
            doc_copy[k] = str(v)
    return doc_copy


router = APIRouter()

# Helper to serialize ObjectId
def serialize_doc(doc):
    doc_copy = dict(doc)
    from bson import ObjectId
    for k, v in doc_copy.items():
        if isinstance(v, ObjectId):
            doc_copy[k] = str(v)
    return doc_copy

@router.get("/courses/{course_id}")
async def course_progress(course_id: str = Path(...), user_id: str = Query(...)):
    """Get progress of a user in a specific course (cached), including completion percentage."""

    cache_key = f"course:{course_id}:user:{user_id}"

    # 1️⃣ Check Redis cache
    cached = await redis_client.get(cache_key)
    if cached:
        return {"cached": True, "data": json.loads(cached)}

    # 2️⃣ Fetch progress document for this user & course
    progress_doc = await db.progress.find_one({
        "user_id": user_id.strip(),
        "course_id": course_id.strip()
    })

    if not progress_doc:
        raise HTTPException(status_code=404, detail="No progress found for this course")

    # 3️⃣ Calculate completion percentage
    lessons = progress_doc.get("lessons", [])
    total_lessons = len(lessons)
    if total_lessons == 0:
        completion_percentage = 0.0
    else:
        completed_lessons = sum(1 for l in lessons if l.get("completed", False))
        completion_percentage = round((completed_lessons / total_lessons) * 100, 2)

    progress_doc["completion_percentage"] = completion_percentage

    # 4️⃣ Serialize ObjectId fields
    progress_doc_serialized = serialize_doc(progress_doc)

    # 5️⃣ Cache the result for 15 minutes
    await redis_client.set(cache_key, json.dumps(progress_doc_serialized), ex=900)

    return {"cached": False, "data": progress_doc_serialized}
