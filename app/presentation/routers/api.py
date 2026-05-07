import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.database.connection import get_session
from app.infrastructure.database.repositories.playlist_repository import SQLAlchemyPlaylistRepository
from app.infrastructure.external.ai_gateway import HttpAIGateway, AIContentError
from app.infrastructure.external.music_gateway import HttpMusicGateway
from app.domain.entities.playlist import Playlist
from app.domain.entities.track import Track
from app.presentation.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Единственные экземпляры gateway
_ai_gateway = HttpAIGateway()
_music_gateway = HttpMusicGateway()


class GenerateRequest(BaseModel):
    prompt: str
    title: str = ""


class PlaylistUpdateRequest(BaseModel):
    title: str
    removed_track_ids: list[int] = []


class PlaylistFavoriteRequest(BaseModel):
    is_favorite: bool


@router.post("/generate")
async def generate(
    data: GenerateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
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
        user_id=current_user.id,
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
        "is_favorite": saved_playlist.is_favorite,
        "tracks": [
            {
                "id": t.id,
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
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = SQLAlchemyPlaylistRepository(session)
    user_playlists = await repo.get_by_user_id(current_user.id)

    return {
        "playlists": [
            {
                "id": p.id,
                "title": p.title,
                "prompt": p.prompt,
                "is_favorite": p.is_favorite,
                "tracks": [
                    {
                        "id": t.id,
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


@router.patch("/playlists/{playlist_id}")
async def update_playlist(
    playlist_id: int,
    data: PlaylistUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    title = data.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Название плейлиста не может быть пустым")

    repo = SQLAlchemyPlaylistRepository(session)
    playlist = await repo.get_by_id(playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Плейлист не найден")

    track_ids = {t.id for t in playlist.tracks}
    for track_id in data.removed_track_ids:
        if track_id in track_ids:
            await repo.delete_track(track_id)

    updated = await repo.update_title(playlist_id, title)
    return {
        "id": updated.id,
        "title": updated.title,
        "prompt": updated.prompt,
        "is_favorite": updated.is_favorite,
        "tracks": [
            {
                "id": t.id,
                "title": t.title,
                "artist": t.artist,
                "duration": _format_duration(t.duration),
                "cover": t.cover_url or "",
                "url": t.url or "",
            }
            for t in updated.tracks
        ],
        "created_at": updated.created_at.isoformat(),
    }


@router.patch("/playlists/{playlist_id}/favorite")
async def update_playlist_favorite(
    playlist_id: int,
    data: PlaylistFavoriteRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = SQLAlchemyPlaylistRepository(session)
    playlist = await repo.get_by_id(playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Плейлист не найден")

    updated = await repo.update_favorite(playlist_id, data.is_favorite)
    return {
        "id": updated.id,
        "is_favorite": updated.is_favorite,
    }


@router.delete("/playlists/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    repo = SQLAlchemyPlaylistRepository(session)
    playlist = await repo.get_by_id(playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Плейлист не найден")

    await repo.delete(playlist_id)
    return {"message": "Плейлист удалён"}
