from abc import ABC, abstractmethod

from app.domain.entities.playlist import Playlist
from app.domain.entities.track import Track


class PlaylistRepository(ABC):
    @abstractmethod
    async def get_by_id(self, playlist_id: int) -> Playlist | None:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> list[Playlist]:
        ...

    @abstractmethod
    async def create(self, playlist: Playlist, tracks: list[Track] | None = None) -> Playlist:
        ...

    @abstractmethod
    async def update_title(self, playlist_id: int, title: str) -> Playlist | None:
        ...

    @abstractmethod
    async def update_favorite(self, playlist_id: int, is_favorite: bool) -> Playlist | None:
        ...

    @abstractmethod
    async def delete(self, playlist_id: int) -> None:
        ...

    @abstractmethod
    async def delete_track(self, track_id: int) -> None:
        ...
