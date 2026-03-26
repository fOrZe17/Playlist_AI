from dataclasses import dataclass


@dataclass
class Track:
    id: int | None = None
    title: str = ""
    artist: str = ""
    url: str | None = None
    cover_url: str | None = None
    duration: int = 0
    playlist_id: int | None = None
