from dataclasses import dataclass


@dataclass
class Track:
    id: int | None = None
    title: str = ""
    artist: str = ""
    url: str | None = None
    playlist_id: int | None = None
