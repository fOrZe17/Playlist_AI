from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    id: int | None = None
    email: str = ""
    hashed_password: str = ""
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    show_email: bool = True
    show_created_at: bool = True
    created_at: datetime = field(default_factory=datetime.now)
