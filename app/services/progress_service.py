# app/services/progress_service.py

from app.utils.cache import invalidate_cache


class ProgressService:
    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client

    async def update_lesson_progress(self, user_id: str, course_id: str, lesson_id: str, time_spent: int,
                                     quiz_score: int):
        # Check if a progress doc already exists
        progress_doc = await self.db.progress.find_one({"user_id": user_id, "course_id": course_id})

        if not progress_doc:
            progress_doc = {"user_id": user_id, "course_id": course_id, "lessons": []}

        # Check if this lesson already exists in progress
        lesson_found = False
        for l in progress_doc["lessons"]:
            if l["lesson_id"] == lesson_id:
                l["completed"] = True
                l["time_spent_seconds"] = l.get("time_spent_seconds", 0) + time_spent
                l.setdefault("quiz_scores", []).append(quiz_score)
                lesson_found = True
                break

        if not lesson_found:
            progress_doc["lessons"].append({
                "lesson_id": lesson_id,
                "completed": True,
                "time_spent_seconds": time_spent,
                "quiz_scores": [quiz_score]
            })

        # Update DB (upsert if doesn't exist)
        await self.db.progress.update_one(
            {"user_id": user_id, "course_id": course_id},
            {"$set": progress_doc},
            upsert=True
        )

        # Invalidate both user dashboard & specific course cache
        invalidate_cache(self.redis, f"progress:{user_id}:{course_id}")
        invalidate_cache(self.redis, f"user_dashboard:{user_id}")
