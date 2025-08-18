from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body
import uuid
from datetime import timedelta
import redis.asyncio as aioredis
from jose import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import UserOut, TokenRequest

from app.dependencies import get_database
import jwt
router = APIRouter()


from fastapi import Body, Depends, HTTPException, status
bearer_scheme = HTTPBearer(auto_error=False)  # don't fail if header missing
router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)  # Allows optional header

# Request model for body (optional in Swagger)
class TokenRequest(BaseModel):
    access_token: str = Field(..., example="your_jwt_token_here")

@router.post("/me", response_model=UserOut, summary="Get Me")
async def get_me(
    request: TokenRequest ,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),  # Optional header
    db=Depends(get_database)
):
    access_token = request.access_token
    # Priority: Bearer header > request body
    # access_token = credentials.credentials if credentials else (request.access_token if request else None)

    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_data = await db["users"].find_one({"_id": user_id})
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return UserOut(
            id=str(user_data["_id"]),
            username=user_data["username"],
            role=user_data["role"]
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
from app.models.user import (
    UserCreate,
    Login,
    UserOut,
    UserUpdate,
    RefreshRequest,
    TokenResponse,
    MessageResponse,
    AccessTokenResponse,
    LogoutResponse,
)

from app.dependencies import (
    get_database,
    get_redis,
    verify_password,
    get_password_hash,  # ✅ added
    create_access_token,
    create_refresh_token,
    cache_user_session, get_current_user,
)

from app.utils.config import settings  # ✅ import settings from its source

router = APIRouter()

# ------------------- Register -------------------
@router.post("/register", response_model=UserOut, summary="Register User")
async def register_user(
    user: UserCreate,
    db=Depends(get_database),
):
    # Ensure username is unique (keep your rule)
    existing = await db["users"].find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    # ✅ hash password before saving
    new_user = {
        "username": user.username,
        "email": getattr(user, "email", None),  # tolerate if model has email
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
            "sub": user.username,
            "role": db_user["role"],
            "jti": token_jti,
            "user_id": str(db_user["_id"]),
        },
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(data={"sub": user.username})

    # Store refresh token in Redis with TTL (in seconds)
    await redis_client.setex(
        f"refresh_token:{user.username}",
        60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        refresh_token,
    )

    # Cache session (async background)
    background_tasks.add_task(cache_user_session, db_user, redis_client)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        "user": UserOut(
            id=str(db_user["_id"]),
            username=db_user["username"],
            role=db_user["role"]
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
        # Decode refresh token
        payload = jwt.decode(
            request.refresh_token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Verify refresh token in Redis
        stored_token = await redis_client.get(f"refresh_token:{username}")
        if not stored_token or stored_token != request.refresh_token:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Verify user exists in DB
        db_user = await db["users"].find_one({"username": username})
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Issue new access token
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

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")



# ------------------- Logout -------------------
@router.post("/logout", response_model=LogoutResponse, summary="Logout User")
async def logout_user(
    request: RefreshRequest,
    redis_client: aioredis.Redis = Depends(get_redis),
):
    deleted = await redis_client.delete(f"refresh_token:{request.username}")
    if not deleted:
        raise HTTPException(status_code=400, detail="User session not found")
    return {"message": "Successfully logged out"}


@router.post("/me", response_model=UserOut)
async def get_me(token: str = Body(...), db=Depends(get_database)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user_data = await db["users"].find_one({"_id": user_id})
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return UserOut(**user_data)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")