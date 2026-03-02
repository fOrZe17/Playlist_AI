from abc import ABC, abstractmethod


class AIGateway(ABC):
    @abstractmethod
    async def generate_playlist_suggestions(self, prompt: str) -> list[dict]:
        """Запрос к AI API для генерации рекомендаций треков."""
        ...
