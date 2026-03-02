from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Схема для регистрации пользователя."""
    email: str
    password: str


class UserRead(BaseModel):
    """Схема для отображения пользователя."""
    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Схема для авторизации пользователя."""
    email: str
    password: str
