# app/services/progress_service.py

from app.utils.cache import invalidate_cache

class ProgressService:
    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client

    async def update_lesson_progress(self, user_id: str, course_id: str, lesson_id: str, time_spent: int, quiz_score: int):

        progress_doc = await self.db.progress.find_one({"user_id": user_id, "course_id": course_id})
        if not progress_doc:
            progress_doc = {"user_id": user_id, "course_id": course_id, "lessons": []}
        # Update lesson
        for l in progress_doc["lessons"]:
            if l["lesson_id"] == lesson_id:
                l["completed"] = True
                l["time_spent_seconds"] += time_spent
                l["quiz_scores"].append(quiz_score)
        await self.db.progress.update_one(
            {"user_id": user_id, "course_id": course_id},
            {"$set": progress_doc},
            upsert=True
        )
        invalidate_cache(self.redis, f"progress:{user_id}:{course_id}")
        invalidate_cache(self.redis, f"user_dashboard:{user_id}")
