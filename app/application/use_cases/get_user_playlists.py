from app.domain.entities.playlist import Playlist
from app.domain.repositories.playlist_repository import PlaylistRepository


class GetUserPlaylists:
    def __init__(self, playlist_repo: PlaylistRepository):
        self._playlist_repo = playlist_repo

    async def execute(self, user_id: int) -> list[Playlist]:
        """Получение всех плейлистов пользователя."""
        return await self._playlist_repo.get_by_user_id(user_id)
