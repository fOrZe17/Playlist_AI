from app.application.interfaces.ai_gateway import AIGateway
from app.application.interfaces.music_gateway import MusicGateway
from app.domain.entities.playlist import Playlist
from app.domain.repositories.playlist_repository import PlaylistRepository


class GeneratePlaylist:
    def __init__(
        self,
        playlist_repo: PlaylistRepository,
        ai_gateway: AIGateway,
        music_gateway: MusicGateway,
    ):
        self._playlist_repo = playlist_repo
        self._ai_gateway = ai_gateway
        self._music_gateway = music_gateway

    async def execute(self, user_id: int, title: str, prompt: str) -> Playlist:
        """Генерация плейлиста с помощью ИИ. TODO: реализовать полную логику."""
        # 1. Получить рекомендации от AI
        # suggestions = await self._ai_gateway.generate_playlist_suggestions(prompt)

        # 2. Найти треки через Music API
        # tracks = []
        # for s in suggestions:
        #     found = await self._music_gateway.search_track(s["query"])
        #     if found:
        #         tracks.append(found[0])

        # 3. Сохранить плейлист
        playlist = Playlist(title=title, user_id=user_id)
        return await self._playlist_repo.create(playlist)
