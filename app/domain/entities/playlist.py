from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Playlist:
    id: int | None = None
    title: str = ""
    prompt: str = ""
    user_id: int | None = None
    is_favorite: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    tracks: list = field(default_factory=list)
