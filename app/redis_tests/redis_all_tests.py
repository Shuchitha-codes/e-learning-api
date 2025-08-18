# app/redis_tests/run_all_tests.py
"""
Run all Redis tests for the E-Learning API
"""

import asyncio
from auth import AuthRedisTests
from courses import CourseRedisTests
from progress import ProgressRedisTests
from analytics import AnalyticsRedisTests


async def run_all_redis_tests():
    """Run all Redis tests sequentially"""
    print("🎯 Starting Complete Redis Test Suite for E-Learning API")
    print("=" * 60)

    # Initialize test classes
    auth_tests = AuthRedisTests()
    course_tests = CourseRedisTests()
    progress_tests = ProgressRedisTests()
    analytics_tests = AnalyticsRedisTests()

    # Run all test suites
    test_results = []

    try:
        print("\n1️⃣ Authentication Tests")
        print("-" * 30)
        await auth_tests.run_all_tests()
        test_results.append("✅ Auth tests passed")
    except Exception as e:
        test_results.append(f"❌ Auth tests failed: {str(e)}")

    try:
        print("\n2️⃣ Course Tests")
        print("-" * 30)
        await course_tests.run_all_tests()
        test_results.append("✅ Course tests passed")
    except Exception as e:
        test_results.append(f"❌ Course tests failed: {str(e)}")

    try:
        print("\n3️⃣ Progress Tests")
        print("-" * 30)
        await progress_tests.run_all_tests()
        test_results.append("✅ Progress tests passed")
    except Exception as e:
        test_results.append(f"❌ Progress tests failed: {str(e)}")

    try:
        print("\n4️⃣ Analytics Tests")
        print("-" * 30)
        await analytics_tests.run_all_tests()
        test_results.append("✅ Analytics tests passed")
    except Exception as e:
        test_results.append(f"❌ Analytics tests failed: {str(e)}")

    # Print summary
    print("\n" + "=" * 60)
    print("🎯 REDIS TEST SUITE SUMMARY")
    print("=" * 60)
    for result in test_results:
        print(result)

    passed_tests = len([r for r in test_results if "✅" in r])
    total_tests = len(test_results)
    print(f"\n📊 Results: {passed_tests}/{total_tests} test suites passed")


if __name__ == "__main__":
    asyncio.run(run_all_redis_tests())