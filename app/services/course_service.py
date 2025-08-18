from app.utils.config import settings
import json
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

class CourseService:
    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client

    async def create_course(self, course_data: dict):
        course_data = jsonable_encoder(course_data)
        result = await self.db.courses.insert_one(course_data)
        await self.invalidate_cache("courses_list:*")
        return str(result.inserted_id)

    async def get_course(self, course_id: str):
        cache_key = f"course:{course_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        course = await self.db.courses.find_one({"_id": ObjectId(course_id)})
        if course:
            await self.redis.set(cache_key, json.dumps(course), ex=settings.COURSE_CACHE_TTL)
        return course

    async def list_courses(self, filters=None):
        filters = filters or {}
        filters_key = str(filters)
        cached = await self.redis.get(f"courses_list:{filters_key}")
        if cached:
            return json.loads(cached)

        courses = await self.db.courses.find(filters).to_list(50)
        await self.redis.set(f"courses_list:{filters_key}", json.dumps(courses), ex=settings.COURSES_LIST_CACHE_TTL)
        return courses

    async def update_course(self, course_id: str, update_data: dict):
        update_data = jsonable_encoder(update_data)
        await self.db.courses.update_one({"_id": ObjectId(course_id)}, {"$set": update_data})
        await self.invalidate_cache(f"course:{course_id}")
        await self.invalidate_cache("courses_list:*")
        return {"message": "Course updated successfully"}

    async def update_module(self, course_id: str, module_id: str, update_data: dict):
        update_data = jsonable_encoder(update_data)
        await self.db.courses.update_one(
            {"_id": ObjectId(course_id), "modules.id": module_id},
            {"$set": {"modules.$": update_data}}
        )
        await self.invalidate_cache(f"course:{course_id}")
        await self.invalidate_cache("courses_list:*")
        return {"message": "Module updated successfully"}

    async def delete_course(self, course_id: str):
        await self.db.courses.delete_one({"_id": ObjectId(course_id)})
        await self.invalidate_cache(f"course:{course_id}")
        await self.invalidate_cache("courses_list:*")
        return {"message": "Course deleted successfully"}

    async def invalidate_cache(self, pattern: str):
        async for key in self.redis.scan_iter(pattern):
            await self.redis.delete(key)
