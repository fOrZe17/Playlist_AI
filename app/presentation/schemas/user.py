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
    display_name: str | None = None
    avatar_url: str | None = None


class UserRead(BaseModel):
    id: int
    email: str
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    show_email: bool = True
    show_created_at: bool = True
    created_at: datetime
    playlists_count: int = 0

    model_config = {"from_attributes": True}


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
