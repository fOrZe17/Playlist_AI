import httpx

from app.application.interfaces.ai_gateway import AIGateway
from app.config import settings


class HttpAIGateway(AIGateway):
    async def generate_playlist_suggestions(self, prompt: str) -> list[dict]:
        """
        Реализация запроса к AI API.
        TODO: реализовать реальный запрос.
        """
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         settings.AI_API_URL,
        #         headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
        #         json={"prompt": prompt},
        #     )
        #     return response.json().get("tracks", [])
        return []
