import json
from datetime import datetime
from app.utils.config import settings

class AnalyticsService:
    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client

    async def course_performance(self, course_id: str):
        cache_key = f"analytics:course:{course_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)  # parse JSON string

        pipeline = [
            {"$match": {"course_id": course_id}},
            {"$unwind": "$lessons"},
            {"$group": {"_id": "$course_id", "avg_score": {"$avg": {"$avg": "$lessons.quiz_scores"}}}}
        ]
        result = await self.db.progress.aggregate(pipeline).to_list(length=None)
        response = {
            "course_id": course_id,
            "avg_score": result[0]["avg_score"] if result else 0,
            "last_cached": datetime.utcnow().isoformat()
        }
        await self.redis.set(cache_key, json.dumps(response), ex=settings.ANALYTICS_COURSE_TTL)
        return response

    async def student_learning_patterns(self, student_id: str):
        cache_key = f"analytics:students:{student_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        records = await self.db.progress.find({"user_id": student_id}).to_list(None)
        lessons_completed = sum(len(r.get("lessons", [])) for r in records)
        avg_quiz_score = (
            sum(
                sum(l.get("quiz_scores", [0])) / len(l.get("quiz_scores", [1]))
                for r in records
                for l in r.get("lessons", [])
            )
            if records else 0
        )
        response = {
            "student_id": student_id,
            "lessons_completed": lessons_completed,
            "avg_quiz_score": avg_quiz_score,
            "engagement_level": "high" if lessons_completed > 0 else "low",
            "last_cached": datetime.utcnow().isoformat()
        }
        await self.redis.set(cache_key, json.dumps(response), ex=1800)  # 30 minutes
        return response

    async def platform_overview(self):
        cache_key = "analytics:platform:overview"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        records = await self.db.progress.find().to_list(None)
        total_students = len(set(r["user_id"] for r in records))
        total_courses = len(set(r["course_id"] for r in records))
        avg_completion_rate = sum(r.get("completion", 0) for r in records) / len(records) if records else 0

        course_counts = {}
        for r in records:
            course_counts[r["course_id"]] = course_counts.get(r["course_id"], 0) + 1
        most_popular_courses = [{"course_id": k, "enrollments": v} for k, v in course_counts.items()]

        response = {
            "total_students": total_students,
            "total_courses": total_courses,
            "avg_completion_rate": avg_completion_rate,
            "most_popular_courses": most_popular_courses,
            "last_cached": datetime.utcnow().isoformat()
        }
        await self.redis.set(cache_key, json.dumps(response), ex=3600)  # 1 hour
        return response
