
import redis.asyncio as aioredis
from app.dependencies import verify_password, create_access_token
from fastapi.security import HTTPBearer
from fastapi.openapi.models import HTTPBearer as HTTPBearerModel

async def authenticate_user(db, username: str, password: str):
    """Authenticate user with username and password"""
    try:
        user = await db["users"].find_one({"username": username})
        if not user:
            return False
        if not verify_password(password, user["password"]):
            return False
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

async def login_user(db, redis_client: aioredis.Redis, username: str, password: str):
    """Login user and create session"""
    try:
        user = await authenticate_user(db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid .env"
            )

        token_jti = str(uuid.uuid4())
        access_token = create_access_token({
            "sub": user["username"],
            "role": user["role"],
            "jti": token_jti
        })

        # Save session in Redis
        await redis_client.setex(f"user_session:{str(user['_id'])}", 86400, str(user))
        await redis_client.setex(f"refresh_tokens:{user['username']}", 604800, access_token)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": access_token,
            "user": user
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

async def logout_user(redis_client: aioredis.Redis, token_jti: str, username: str):
    """Logout user and blacklist token"""
    try:
        await redis_client.setex(f"blacklisted_tokens:{token_jti}", 86400, "1")
        await redis_client.delete(f"refresh_tokens:{username}")
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


import uuid
from fastapi import HTTPException, status


async def refresh_token(db, redis_client, refresh_token: str, verify_token_func, create_access_token_func):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_token_func(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Check if refresh token exists in Redis
        stored_token = await redis_client.get(f"refresh_tokens:{username}")
        if stored_token != refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired"
            )

        # Get user from database
        user = await db.users.find_one({"username": username})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Create new access token
        token_jti = str(uuid.uuid4())
        new_access_token = create_access_token_func({
            "sub": user["username"],
            "role": user["role"],
            "jti": token_jti
        })

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


async def validate_token_against_redis(redis_client, username: str, token_jti: str):
    """Validate token against Redis session"""
    try:
        # Check if user session exists
        session = await redis_client.get(f"user_session:{username}")
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )

        # Check if token is blacklisted
        is_blacklisted = await redis_client.get(f"blacklisted_tokens:{token_jti}")
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token validation failed: {str(e)}"
        )