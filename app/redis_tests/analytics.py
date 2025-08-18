# app/redis_tests/analytics.py
"""
Redis tests for analytics functionality
Tests: analytics caching, platform overview, performance metrics
"""

import asyncio
import json
import redis.asyncio as aioredis
from app.utils.config import settings


class AnalyticsRedisTests:
    def __init__(self):
        self.redis_client = None

    async def setup(self):
        """Initialize Redis connection"""
        self.redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        print("✅ Redis connection established for analytics tests")

    async def cleanup(self):
        """Clean up test data"""
        await self.redis_client.flushdb()
        await self.redis_client.close()
        print("🧹 Analytics test data cleaned up")

    async def test_course_performance_caching(self):
        """Test course performance analytics caching"""
        print("\n📋 Testing course performance caching...")

        course_id = "course_123"
        performance_data = {
            "course_id": course_id,
            "total_enrollments": 250,
            "avg_completion_rate": 78.5,
            "avg_quiz_score": 85.2,
            "avg_time_per_lesson": 1200,
            "most_difficult_lessons": ["lesson_5", "lesson_8"],
            "completion_by_module": {
                "module_1": 95.0,
                "module_2": 82.0,
                "module_3": 68.0
            }
        }

        # Cache performance data
        key = f"analytics:course:{course_id}"
        await self.redis_client.setex(key, settings.ANALYTICS_COURSE_TTL, json.dumps(performance_data))

        # Retrieve performance data
        cached_data = await self.redis_client.get(key)
        assert cached_data is not None
        assert json.loads(cached_data) == performance_data

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ Course performance cached successfully, TTL: {ttl}s")

    async def test_student_learning_patterns_caching(self):
        """Test student learning patterns caching"""
        print("\n📋 Testing student learning patterns caching...")

        student_id = "student_456"
        patterns_data = {
            "student_id": student_id,
            "preferred_learning_time": "evening",
            "avg_session_duration": 2400,
            "learning_velocity": "moderate",
            "strong_subjects": ["programming", "databases"],
            "areas_for_improvement": ["algorithms"],
            "engagement_score": 8.5,
            "completion_patterns": {
                "weekdays": 70.0,
                "weekends": 85.0
            }
        }

        # Cache patterns
        key = f"analytics:student:{student_id}"
        await self.redis_client.setex(key, 1800, json.dumps(patterns_data))  # 30 min TTL

        # Retrieve patterns
        cached_patterns = await self.redis_client.get(key)
        assert cached_patterns is not None
        assert json.loads(cached_patterns) == patterns_data

        print("✅ Student learning patterns cached successfully")

    async def test_platform_overview_caching(self):
        """Test platform overview analytics caching"""
        print("\n📋 Testing platform overview caching...")

        overview_data = {
            "total_users": 1250,
            "total_courses": 45,
            "total_enrollments": 3200,
            "avg_course_completion": 72.5,
            "monthly_active_users": 890,
            "top_categories": [
                {"category": "Programming", "courses": 15, "enrollments": 1200},
                {"category": "Data Science", "courses": 10, "enrollments": 800},
                {"category": "Design", "courses": 8, "enrollments": 600}
            ],
            "revenue_metrics": {
                "monthly_revenue": 15000,
                "avg_revenue_per_user": 45.50
            }
        }

        # Cache overview
        key = "analytics:platform:overview"
        await self.redis_client.setex(key, settings.ANALYTICS_PLATFORM_TTL, json.dumps(overview_data))

        # Retrieve overview
        cached_overview = await self.redis_client.get(key)
        assert cached_overview is not None
        assert json.loads(cached_overview) == overview_data

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ Platform overview cached successfully, TTL: {ttl}s")

    async def test_search_results_caching(self):
        """Test search results caching"""
        print("\n📋 Testing search results caching...")

        query_hash = "python_fastapi_123"
        search_results = {
            "query": "python fastapi",
            "total_results": 12,
            "courses": [
                {"id": "course1", "title": "Python FastAPI Basics", "relevance": 95},
                {"id": "course2", "title": "Advanced FastAPI", "relevance": 88}
            ],
            "filters_applied": ["category:programming"],
            "search_time_ms": 45
        }

        # Cache search results
        key = f"search:{query_hash}"
        await self.redis_client.setex(key, 1800, json.dumps(search_results))  # 30 min TTL

        # Retrieve search results
        cached_results = await self.redis_client.get(key)
        assert cached_results is not None
        assert json.loads(cached_results) == search_results

        print("✅ Search results cached successfully")

    async def run_all_tests(self):
        """Run all analytics Redis tests"""
        print("🚀 Starting Analytics Redis Tests...")
        await self.setup()

        try:
            await self.test_course_performance_caching()
            await self.test_student_learning_patterns_caching()
            await self.test_platform_overview_caching()
            await self.test_search_results_caching()
            print("\n✅ All analytics Redis tests passed!")
        except Exception as e:
            print(f"\n❌ Analytics test failed: {str(e)}")
        finally:
            await self.cleanup()


# Run tests if called directly
if __name__ == "__main__":
    test = AnalyticsRedisTests()
    asyncio.run(test.run_all_tests())