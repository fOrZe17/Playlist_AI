import logging

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.auth import decode_access_token
from app.infrastructure.database.connection import get_session
from app.infrastructure.database.repositories.playlist_repository import SQLAlchemyPlaylistRepository
from app.infrastructure.external.ai_gateway import HttpAIGateway, AIContentError
from app.infrastructure.external.music_gateway import HttpMusicGateway
from app.domain.entities.playlist import Playlist
from app.domain.entities.track import Track

logger = logging.getLogger(__name__)

router = APIRouter()

# Единственные экземпляры gateway
_ai_gateway = HttpAIGateway()
_music_gateway = HttpMusicGateway()


def _get_user_id_from_token(authorization: str | None) -> int | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        return int(payload["sub"])
    return None


class GenerateRequest(BaseModel):
    prompt: str
    title: str = ""


@router.post("/generate")
async def generate(
    data: GenerateRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    user_id = _get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    # Генерация треков через Gemini AI
    try:
        suggestions = await _ai_gateway.generate_playlist_suggestions(data.prompt)
    except AIContentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Ошибка при обращении к Gemini: %s", e)
        raise HTTPException(status_code=502, detail="Ошибка генерации плейлиста")

    # Обогащение треков через Deezer API
    enriched = await _music_gateway.enrich_tracks(suggestions)

    if not enriched:
        raise HTTPException(
            status_code=400,
            detail="Не удалось найти треки. Попробуйте другой запрос.",
        )

    title = data.title or f"Плейлист: {data.prompt[:40]}"

    # Сохранение в PostgreSQL
    playlist_entity = Playlist(
        title=title,
        prompt=data.prompt,
        user_id=user_id,
    )
    track_entities = [
        Track(
            title=t.get("title", ""),
            artist=t.get("artist", ""),
            url=t.get("url"),
            cover_url=t.get("cover_url"),
            duration=t.get("duration", 0),
        )
        for t in enriched
    ]

    repo = SQLAlchemyPlaylistRepository(session)
    saved_playlist = await repo.create(playlist_entity, track_entities)

    # Возвращаем ответ в формате, ожидаемом фронтендом
    return {
        "id": saved_playlist.id,
        "title": saved_playlist.title,
        "prompt": saved_playlist.prompt,
        "tracks": [
            {
                "title": t.title,
                "artist": t.artist,
                "duration": _format_duration(t.duration),
                "cover": t.cover_url or "🎵",
                "url": t.url or "",
            }
            for t in saved_playlist.tracks
        ],
        "created_at": saved_playlist.created_at.isoformat(),
    }


def _format_duration(seconds: int) -> str:
    """Форматирование длительности из секунд в мм:сс."""
    if not seconds:
        return ""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


@router.get("/playlists")
async def playlists(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
):
    user_id = _get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    repo = SQLAlchemyPlaylistRepository(session)
    user_playlists = await repo.get_by_user_id(user_id)

    return {
        "playlists": [
            {
                "id": p.id,
                "title": p.title,
                "prompt": p.prompt,
                "tracks": [
                    {
                        "title": t.title,
                        "artist": t.artist,
                        "duration": _format_duration(t.duration),
                        "cover": t.cover_url or "🎵",
                        "url": t.url or "",
                    }
                    for t in p.tracks
                ],
                "created_at": p.created_at.isoformat(),
            }
            for p in user_playlists
        ]
    }
