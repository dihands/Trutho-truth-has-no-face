from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


# ── Auth ──────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: Optional[str] = None
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    user_id: int


class UserOut(BaseModel):
    id: int
    username: str
    reputation: int
    created_at: datetime
    is_admin: bool

    class Config:
        from_attributes = True


# ── Posts ─────────────────────────────────────────────
class PostCreate(BaseModel):
    title: str
    body: str
    category: str

    @field_validator("title")
    @classmethod
    def title_length(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Title too short")
        if len(v) > 300:
            raise ValueError("Title too long")
        return v.strip()

    @field_validator("body")
    @classmethod
    def body_length(cls, v):
        if len(v.strip()) < 20:
            raise ValueError("Report body too short — minimum 20 characters")
        return v.strip()


class PostOut(BaseModel):
    id: int
    title: str
    body: str
    category: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    author_username: Optional[str] = None
    likes: int
    dislikes: int
    views: int
    trending_score: float
    verification_status: str
    created_at: datetime
    comment_count: int = 0

    class Config:
        from_attributes = True


# ── Comments ──────────────────────────────────────────
class CommentCreate(BaseModel):
    body: str

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Comment too short")
        return v.strip()


class CommentOut(BaseModel):
    id: int
    post_id: int
    author_username: Optional[str] = None
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Reactions ─────────────────────────────────────────
class ReactionOut(BaseModel):
    message: str
    likes: int
    dislikes: int
