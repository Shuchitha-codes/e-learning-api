# app/redis_tests/auth.py
"""
Redis tests for authentication functionality
Tests: session management, token blacklisting, refresh tokens
"""

import asyncio
import json
import redis.asyncio as aioredis
from app.utils.config import settings


class AuthRedisTests:
    def __init__(self):
        self.redis_client = None

    async def setup(self):
        """Initialize Redis connection"""
        self.redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        print("✅ Redis connection established for auth tests")

    async def cleanup(self):
        """Clean up test data"""
        await self.redis_client.flushdb()
        await self.redis_client.close()
        print("🧹 Auth test data cleaned up")

    async def test_user_session_cache(self):
        """Test user session caching"""
        print("\n📋 Testing user session caching...")

        # Test data
        user_id = "test_user_123"
        user_data = {
            "username": "testuser",
            "role": "student",
            "email": "test@example.com"
        }

        # Set session
        key = f"user_session:{user_id}"
        await self.redis_client.setex(key, 86400, json.dumps(user_data))

        # Retrieve session
        cached_data = await self.redis_client.get(key)
        assert cached_data is not None
        assert json.loads(cached_data) == user_data

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ User session cached successfully, TTL: {ttl}s")

    async def test_token_blacklisting(self):
        """Test JWT token blacklisting"""
        print("\n📋 Testing token blacklisting...")

        token_jti = "test_token_jti_456"
        key = f"blacklisted_tokens:{token_jti}"

        # Blacklist token
        await self.redis_client.setex(key, 3600, "1")

        # Check if blacklisted
        is_blacklisted = await self.redis_client.get(key)
        assert is_blacklisted == "1"

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ Token blacklisted successfully, TTL: {ttl}s")

    async def test_refresh_token_storage(self):
        """Test refresh token storage"""
        print("\n📋 Testing refresh token storage...")

        username = "testuser"
        refresh_token = "test_refresh_token_789"
        key = f"refresh_token:{username}"

        # Store refresh token
        await self.redis_client.setex(key, 604800, refresh_token)  # 7 days

        # Retrieve refresh token
        stored_token = await self.redis_client.get(key)
        assert stored_token == refresh_token

        # Check TTL
        ttl = await self.redis_client.ttl(key)
        assert ttl > 0

        print(f"✅ Refresh token stored successfully, TTL: {ttl}s")

    async def run_all_tests(self):
        """Run all auth Redis tests"""
        print("🚀 Starting Auth Redis Tests...")
        await self.setup()

        try:
            await self.test_user_session_cache()
            await self.test_token_blacklisting()
            await self.test_refresh_token_storage()
            print("\n✅ All auth Redis tests passed!")
        except Exception as e:
            print(f"\n❌ Auth test failed: {str(e)}")
        finally:
            await self.cleanup()


# Run tests if called directly
if __name__ == "__main__":
    test = AuthRedisTests()
    asyncio.run(test.run_all_tests())
