import httpx

from app.application.interfaces.music_gateway import MusicGateway
from app.config import settings


class HttpMusicGateway(MusicGateway):
    async def search_track(self, query: str) -> list[dict]:
        """
        Реализация поиска трека через Music API.
        TODO: реализовать реальный запрос.
        """
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{settings.MUSIC_API_URL}/search",
        #         headers={"Authorization": f"Bearer {settings.MUSIC_API_KEY}"},
        #         params={"q": query},
        #     )
        #     return response.json().get("results", [])
        return []

    async def get_track_info(self, track_id: str) -> dict | None:
        """
        Реализация получения информации о треке.
        TODO: реализовать реальный запрос.
        """
        return None
