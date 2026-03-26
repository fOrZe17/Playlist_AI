import json
import re

import httpx

from app.application.interfaces.ai_gateway import AIGateway
from app.config import settings

SYSTEM_PROMPT = (
    "Ты — музыкальный помощник для сервиса создания плейлистов. "
    "Твоя единственная задача — составлять музыкальные плейлисты. "
    "На основе запроса пользователя сформируй список музыкальных композиций. "
    'Отвечай ТОЛЬКО в формате JSON-массива: [{"title": "название трека", "artist": "исполнитель"}]. '
    "Если пользователь не указал количество треков, сгенерируй 10. "
    "Называй ТОЛЬКО реально существующие треки и исполнителей. "
    "НЕ выдумывай названия треков — если не знаешь точных названий треков исполнителя, "
    "лучше честно верни меньше треков чем выдумывать несуществующие. "
    "Если пользователь просит треки конкретного артиста — постарайся вспомнить именно его реальные треки. "
    "Если запрос пользователя НЕ связан с музыкой, плейлистами или подбором песен — верни JSON: "
    '{"error": "Ваш запрос не связан с созданием музыкального плейлиста. '
    'Пожалуйста, опишите какую музыку вы хотите услышать."}. '
    "Если запрос содержит только числа без описания музыки — верни ту же ошибку. "
    "Никогда не отвечай на вопросы не связанные с музыкой. Не добавляй пояснений, только JSON."
)

INVALID_PROMPT_MESSAGE = (
    "Пожалуйста, опишите какую музыку вы хотите услышать"
)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3-flash-preview:generateContent"
)


class HttpAIGateway(AIGateway):

    @staticmethod
    def _validate_prompt(prompt: str) -> None:
        """Валидация запроса перед отправкой в Gemini."""
        stripped = prompt.strip()
        if len(stripped) < 3:
            raise AIContentError(INVALID_PROMPT_MESSAGE)
        if re.fullmatch(r"[\d\s\W]+", stripped):
            raise AIContentError(INVALID_PROMPT_MESSAGE)

    async def generate_playlist_suggestions(self, prompt: str) -> list[dict]:
        """Запрос к Google Gemini для генерации рекомендаций треков."""
        self._validate_prompt(prompt)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    GEMINI_URL,
                    params={"key": settings.AI_API_KEY},
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {"role": "user", "parts": [{"text": prompt}]},
                        ],
                        "systemInstruction": {
                            "parts": [{"text": SYSTEM_PROMPT}],
                        },
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (401, 403):
                    raise AIContentError(
                        "Ошибка авторизации API. Проверьте ключ AI_API_KEY."
                    )
                raise AIContentError(
                    "Сервис ИИ временно недоступен. Попробуйте позже."
                )
            except httpx.RequestError:
                raise AIContentError(
                    "Не удалось подключиться к сервису ИИ. Попробуйте позже."
                )

            data = response.json()

        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise AIContentError(
                "Не удалось получить ответ от ИИ. Попробуйте ещё раз."
            )

        return self._parse_response(content)

    @staticmethod
    def _parse_response(content: str) -> list[dict]:
        """Извлечение JSON из текстового ответа Gemini."""
        cleaned = re.sub(r"```(?:json)?\s*", "", content).strip().rstrip("`")

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            raise AIContentError(
                "Ваш запрос не связан с созданием музыкального плейлиста. "
                "Пожалуйста, опишите какую музыку вы хотите услышать."
            )

        if isinstance(parsed, dict) and "error" in parsed:
            raise AIContentError(parsed["error"])

        if not isinstance(parsed, list):
            raise AIContentError(
                "Ваш запрос не связан с созданием музыкального плейлиста. "
                "Пожалуйста, опишите какую музыку вы хотите услышать."
            )

        return parsed


class AIContentError(Exception):
    """Ошибка контента от AI (не связанный с музыкой запрос и т.п.)."""
    pass
