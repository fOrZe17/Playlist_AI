from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str
    email: str


class UserRead(BaseModel):
    id: int
    email: str
    created_at: datetime
    playlists_count: int = 0

    model_config = {"from_attributes": True}
