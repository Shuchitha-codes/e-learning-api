# app/routes/auth.py

from datetime import timedelta
import uuid

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
import redis.asyncio as aioredis

from app.models.user import (
    UserCreate,
    Login,
    UserOut,
    UserUpdate,             # kept for future use
    RefreshRequest,
    TokenResponse,
    MessageResponse,        # kept for future use
    AccessTokenResponse,
    LogoutResponse,
)
from pydantic import BaseModel, Field

from app.dependencies import (
    get_database,
    get_redis,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    cache_user_session,
)
from app.utils.config import settings


# ------------------- Setup -------------------
router = APIRouter()


# ------------------- Request Models -------------------
class TokenRequest(BaseModel):
    access_token: str = Field(..., example="your_jwt_token_here")


class LogoutRequest(BaseModel):
    # Option A (recommended): pass the refresh token so we can derive username
    refresh_token: str | None = None
    # Option B: if you prefer, allow explicit username (used only if no refresh_token given)
    username: str | None = None


# ------------------- Register -------------------
@router.post("/register", response_model=UserOut, summary="Register User")
async def register_user(
    user: UserCreate,
    db=Depends(get_database),
):
    existing = await db["users"].find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = {
        "username": user.username,
        "email": getattr(user, "email", None),
        "password": get_password_hash(user.password),
        "role": user.role,
    }

    result = await db["users"].insert_one(new_user)
    return UserOut(id=str(result.inserted_id), username=user.username, role=user.role)


# ------------------- Login -------------------
@router.post("/login", response_model=TokenResponse, summary="Login User")
async def login_user(
    user: Login,
    background_tasks: BackgroundTasks,
    db=Depends(get_database),
    redis_client: aioredis.Redis = Depends(get_redis),
):
    db_user = await db["users"].find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token_jti = str(uuid.uuid4())
    access_token = create_access_token(
        data={
            # Keep `sub` = username (your current choice)
            "sub": db_user["username"],
            "role": db_user["role"],
            "jti": token_jti,
            # Crucial for /auth/me:
            "user_id": str(db_user["_id"]),
        },
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(data={"sub": db_user["username"]})

    # Store refresh token in Redis with TTL (seconds)
    await redis_client.setex(
        f"refresh_token:{db_user['username']}",
        60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        refresh_token,
    )

    # Cache session in background
    background_tasks.add_task(cache_user_session, db_user, redis_client)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        "user": UserOut(
            id=str(db_user["_id"]),
            username=db_user["username"],
            role=db_user["role"],
        ),
    }


# ------------------- Refresh -------------------
@router.post("/refresh", response_model=AccessTokenResponse, summary="Refresh Access Token")
async def refresh_token(
    request: RefreshRequest,
    db=Depends(get_database),
    redis_client: aioredis.Redis = Depends(get_redis),
):
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        stored_token = await redis_client.get(f"refresh_token:{username}")
        if not stored_token or stored_token != request.refresh_token:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        db_user = await db["users"].find_one({"username": username})
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        token_jti = str(uuid.uuid4())
        access_token = create_access_token(
            data={
                "sub": username,
                "role": db_user["role"],
                "jti": token_jti,
                "user_id": str(db_user["_id"]),
            },
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        }

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


# ------------------- Logout -------------------
@router.post("/logout", response_model=LogoutResponse, summary="Logout User")
async def logout_user(
    request: LogoutRequest,
    redis_client: aioredis.Redis = Depends(get_redis),
):
    # Prefer deriving username from refresh token if provided
    username = request.username
    if request.refresh_token:
        try:
            payload = jwt.decode(
                request.refresh_token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            username = payload.get("sub") or username
        except JWTError:
            pass  # fall back to provided username if any

    if not username:
        raise HTTPException(status_code=400, detail="Username or valid refresh_token required")

    deleted = await redis_client.delete(f"refresh_token:{username}")
    if not deleted:
        raise HTTPException(status_code=400, detail="User session not found")

    return {"message": "Successfully logged out", "username": username}


# ------------------- Me (Body token as requested) -------------------
@router.post("/me", response_model=UserOut, summary="Get current user")
async def get_me(
    token: TokenRequest = Body(...),
    db=Depends(get_database),
):
    """
    Accepts a JSON body like:
    {
      "access_token": "<JWT>"
    }
    """
    try:
        payload = jwt.decode(
            token.access_token,
            settings.JWT_SECRET,           # MUST match login() secret
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: user_id missing")

        user_data = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return UserOut(
            id=str(user_data["_id"]),
            username=user_data["username"],
            role=user_data["role"],
        )

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
