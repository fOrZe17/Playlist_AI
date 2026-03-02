from datetime import datetime

from pydantic import BaseModel


class TrackBase(BaseModel):
    """Базовая схема трека."""
    title: str
    artist: str
    url: str | None = None


class PlaylistCreate(BaseModel):
    """Схема для создания плейлиста."""
    title: str
    prompt: str


class PlaylistRead(BaseModel):
    """Схема для отображения плейлиста."""
    id: int
    title: str
    created_at: datetime
    tracks: list[TrackBase] = []

    model_config = {"from_attributes": True}
