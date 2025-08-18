# app/redis_tests/courses.py
"""
Redis tests for course functionality
Tests: course caching, course list caching, cache invalidation
"""

import asyncio
import json
import redis.asyncio as aioredis
from app.utils.config import settings


class CourseRedisTests:
    def __init__(self):
        self.redis_client = None

    async def setup(self):
        """Initialize Redis connection"""
        self.redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        print("✅ Redis connection established for course tests")

    async def cleanup(self):
        """Clean up test data"""
        await self.redis_client.flushdb()
        await self.redis_client.close()
        print("🧹 Course test data cleaned up")

    async def test_course_caching(self):
        """Test individual course caching"""
        print("\n📋 Testing course caching...")

        course_id = "test_course_123"
        course_data = {
            "id": course_id,
            "title": "Test Course",
            "description": "A test course",
            "category": "Programming",
            "tags": ["python", "fastapi"],
            "instructor_id": "instructor_123",
            "modules": []
        }

        # Cache course
        key = f"course:{course_id}"
        await self.redis_client.setex(key, settings.COURSE_CACHE_TTL, json.dumps(course_data))

        # Retrieve course
        cached_course = await self.redis_client.get(key)
        assert cached_course is not None
        assert json.loads(cached_course) == course_data

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ Course cached successfully, TTL: {ttl}s")

    async def test_courses_list_caching(self):
        """Test course list caching with filters"""
        print("\n📋 Testing course list caching...")

        filters_hash = "category_programming"
        courses_data = [
            {"id": "course1", "title": "Python Basics", "category": "Programming"},
            {"id": "course2", "title": "FastAPI Advanced", "category": "Programming"}
        ]

        # Cache course list
        key = f"courses_list:{filters_hash}"
        await self.redis_client.setex(key, settings.COURSES_LIST_CACHE_TTL, json.dumps(courses_data))

        # Retrieve course list
        cached_courses = await self.redis_client.get(key)
        assert cached_courses is not None
        assert json.loads(cached_courses) == courses_data

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ Course list cached successfully, TTL: {ttl}s")

    async def test_popular_courses_caching(self):
        """Test popular courses caching"""
        print("\n📋 Testing popular courses caching...")

        popular_courses = [
            {"id": "popular1", "title": "Most Popular Course", "enrollments": 1000},
            {"id": "popular2", "title": "Second Popular", "enrollments": 800}
        ]

        # Cache popular courses
        key = "popular_courses"
        await self.redis_client.setex(key, settings.POPULAR_COURSES_TTL, json.dumps(popular_courses))

        # Retrieve popular courses
        cached_popular = await self.redis_client.get(key)
        assert cached_popular is not None
        assert json.loads(cached_popular) == popular_courses

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ Popular courses cached successfully, TTL: {ttl}s")

    async def test_cache_invalidation(self):
        """Test cache invalidation patterns"""
        print("\n📋 Testing cache invalidation...")

        # Set multiple cache keys
        keys_to_invalidate = [
            "course:123",
            "courses_list:category_programming",
            "courses_list:all"
        ]

        for key in keys_to_invalidate:
            await self.redis_client.setex(key, 300, "test_data")

        # Verify keys exist
        for key in keys_to_invalidate:
            assert await self.redis_client.exists(key) == 1

        # Invalidate all course-related cache
        pattern = "course*"
        keys = []
        async for key in self.redis_client.scan_iter(pattern):
            keys.append(key)

        if keys:
            await self.redis_client.delete(*keys)

        # Verify keys are deleted
        for key in keys_to_invalidate:
            assert await self.redis_client.exists(key) == 0

        print("✅ Cache invalidation successful")

    async def run_all_tests(self):
        """Run all course Redis tests"""
        print("🚀 Starting Course Redis Tests...")
        await self.setup()

        try:
            await self.test_course_caching()
            await self.test_courses_list_caching()
            await self.test_popular_courses_caching()
            await self.test_cache_invalidation()
            print("\n✅ All course Redis tests passed!")
        except Exception as e:
            print(f"\n❌ Course test failed: {str(e)}")
        finally:
            await self.cleanup()


# Run tests if called directly
if __name__ == "__main__":
    test = CourseRedisTests()
    asyncio.run(test.run_all_tests())

