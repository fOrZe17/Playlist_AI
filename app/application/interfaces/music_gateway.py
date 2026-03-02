from abc import ABC, abstractmethod


class MusicGateway(ABC):
    @abstractmethod
    async def search_track(self, query: str) -> list[dict]:
        """Поиск трека через API музыкального сервиса."""
        ...

    @abstractmethod
    async def get_track_info(self, track_id: str) -> dict | None:
        """Получение информации о треке."""
        ...
