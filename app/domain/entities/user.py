from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    id: int | None = None
    email: str = ""
    hashed_password: str = ""
    created_at: datetime = field(default_factory=datetime.now)
