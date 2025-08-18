# app/redis_tests/progress.py
"""
Redis tests for progress functionality
Tests: user progress caching, dashboard caching, course progress
"""

import asyncio
import json
import redis.asyncio as aioredis
from app.utils.config import settings


class ProgressRedisTests:
    def __init__(self):
        self.redis_client = None

    async def setup(self):
        """Initialize Redis connection"""
        self.redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        print("✅ Redis connection established for progress tests")

    async def cleanup(self):
        """Clean up test data"""
        await self.redis_client.flushdb()
        await self.redis_client.close()
        print("🧹 Progress test data cleaned up")

    async def test_user_progress_caching(self):
        """Test user progress caching per course"""
        print("\n📋 Testing user progress caching...")

        user_id = "user_123"
        course_id = "course_456"
        progress_data = {
            "user_id": user_id,
            "course_id": course_id,
            "lessons": [
                {
                    "lesson_id": "lesson_1",
                    "completed": True,
                    "time_spent_seconds": 1800,
                    "quiz_scores": [85, 90]
                },
                {
                    "lesson_id": "lesson_2",
                    "completed": False,
                    "time_spent_seconds": 600,
                    "quiz_scores": []
                }
            ],
            "completion_percentage": 50.0
        }

        # Cache progress
        key = f"progress:{user_id}:{course_id}"
        await self.redis_client.setex(key, settings.USER_PROGRESS_CACHE_TTL, json.dumps(progress_data))

        # Retrieve progress
        cached_progress = await self.redis_client.get(key)
        assert cached_progress is not None
        assert json.loads(cached_progress) == progress_data

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ User progress cached successfully, TTL: {ttl}s")

    async def test_user_dashboard_caching(self):
        """Test user dashboard data caching"""
        print("\n📋 Testing user dashboard caching...")

        user_id = "user_123"
        dashboard_data = {
            "total_courses": 5,
            "completed_courses": 2,
            "in_progress_courses": 3,
            "total_time_spent": 18000,
            "current_streak": 7,
            "achievements": ["First Course", "Week Streak"],
            "recent_activity": [
                {"course_id": "course1", "lesson_id": "lesson1", "completed_at": "2025-01-15T10:00:00"},
                {"course_id": "course2", "lesson_id": "lesson3", "completed_at": "2025-01-14T15:30:00"}
            ]
        }

        # Cache dashboard
        key = f"user_dashboard:{user_id}"
        await self.redis_client.setex(key, settings.USER_DASHBOARD_CACHE_TTL, json.dumps(dashboard_data))

        # Retrieve dashboard
        cached_dashboard = await self.redis_client.get(key)
        assert cached_dashboard is not None
        assert json.loads(cached_dashboard) == dashboard_data

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ User dashboard cached successfully, TTL: {ttl}s")

    async def test_learning_streaks_caching(self):
        """Test learning streaks and milestones caching"""
        print("\n📋 Testing learning streaks caching...")

        user_id = "user_123"
        streak_data = {
            "current_streak": 15,
            "longest_streak": 30,
            "streak_start_date": "2025-01-01",
            "milestones": [
                {"type": "week_streak", "achieved_at": "2025-01-07"},
                {"type": "month_streak", "achieved_at": "2025-01-31"}
            ]
        }

        # Cache streaks
        key = f"learning_streaks:{user_id}"
        await self.redis_client.setex(key, 3600, json.dumps(streak_data))  # 1 hour TTL

        # Retrieve streaks
        cached_streaks = await self.redis_client.get(key)
        assert cached_streaks is not None
        assert json.loads(cached_streaks) == streak_data

        print("✅ Learning streaks cached successfully")

    async def test_progress_cache_invalidation(self):
        """Test progress cache invalidation on updates"""
        print("\n📋 Testing progress cache invalidation...")

        user_id = "user_123"
        course_id = "course_456"

        # Set multiple related cache keys
        keys = [
            f"progress:{user_id}:{course_id}",
            f"user_dashboard:{user_id}",
            f"learning_streaks:{user_id}"
        ]

        for key in keys:
            await self.redis_client.setex(key, 600, "test_data")

        # Verify all keys exist
        for key in keys:
            assert await self.redis_client.exists(key) == 1

        # Simulate progress update - invalidate related caches
        for key in keys:
            await self.redis_client.delete(key)

        # Verify keys are deleted
        for key in keys:
            assert await self.redis_client.exists(key) == 0

        print("✅ Progress cache invalidation successful")

    async def run_all_tests(self):
        """Run all progress Redis tests"""
        print("🚀 Starting Progress Redis Tests...")
        await self.setup()

        try:
            await self.test_user_progress_caching()
            await self.test_user_dashboard_caching()
            await self.test_learning_streaks_caching()
            await self.test_progress_cache_invalidation()
            print("\n✅ All progress Redis tests passed!")
        except Exception as e:
            print(f"\n❌ Progress test failed: {str(e)}")
        finally:
            await self.cleanup()


# Run tests if called directly
if __name__ == "__main__":
    test = ProgressRedisTests()
    asyncio.run(test.run_all_tests())