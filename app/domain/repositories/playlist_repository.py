from abc import ABC, abstractmethod

from app.domain.entities.playlist import Playlist


class PlaylistRepository(ABC):
    @abstractmethod
    async def get_by_id(self, playlist_id: int) -> Playlist | None:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> list[Playlist]:
        ...

    @abstractmethod
    async def create(self, playlist: Playlist) -> Playlist:
        ...

    @abstractmethod
    async def delete(self, playlist_id: int) -> None:
        ...
