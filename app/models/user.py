from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ------------------- User Role -------------------
class UserRole(str, Enum):
    admin = "admin"
    instructor = "instructor"
    student = "student"


# ------------------- User Models -------------------
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.student


class UserCreate(UserBase):
    password: str


class Login(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    role: UserRole


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None

class ListUsersOut(BaseModel):
    users: List[UserOut]
    total: int


# ------------------- Auth & Response Models -------------------
class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int
    user: Optional["UserOut"] = None


class MessageResponse(BaseModel):
    message: str
    username: Optional[str] = None


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class LogoutResponse(BaseModel):
    message: str
    username: str

class TokenRequest(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")





# ------------------- Pydantic v2 forward refs fix -------------------
TokenResponse.model_rebuild()