import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.auth import decode_access_token
from app.infrastructure.database.connection import get_session
from app.infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.database.repositories.playlist_repository import SQLAlchemyPlaylistRepository
from app.domain.entities.playlist import Playlist
from app.domain.entities.track import Track

router = APIRouter()

MOCK_TRACKS = [
    {"title": "Blinding Lights", "artist": "The Weeknd", "duration": "3:20", "cover": "🌆"},
    {"title": "Bohemian Rhapsody", "artist": "Queen", "duration": "5:55", "cover": "👑"},
    {"title": "Shape of You", "artist": "Ed Sheeran", "duration": "3:53", "cover": "🎸"},
    {"title": "Starboy", "artist": "The Weeknd", "duration": "3:50", "cover": "⭐"},
    {"title": "Levitating", "artist": "Dua Lipa", "duration": "3:23", "cover": "🚀"},
    {"title": "Watermelon Sugar", "artist": "Harry Styles", "duration": "2:54", "cover": "🍉"},
    {"title": "Save Your Tears", "artist": "The Weeknd", "duration": "3:35", "cover": "💧"},
    {"title": "Peaches", "artist": "Justin Bieber", "duration": "3:18", "cover": "🍑"},
    {"title": "Good 4 U", "artist": "Olivia Rodrigo", "duration": "2:58", "cover": "🔥"},
    {"title": "Stay", "artist": "The Kid LAROI & Justin Bieber", "duration": "2:21", "cover": "💜"},
    {"title": "Montero", "artist": "Lil Nas X", "duration": "2:17", "cover": "🦋"},
    {"title": "Kiss Me More", "artist": "Doja Cat ft. SZA", "duration": "3:28", "cover": "💋"},
    {"title": "drivers license", "artist": "Olivia Rodrigo", "duration": "4:02", "cover": "🚗"},
    {"title": "Positions", "artist": "Ariana Grande", "duration": "2:52", "cover": "✨"},
    {"title": "Dynamite", "artist": "BTS", "duration": "3:19", "cover": "💣"},
    {"title": "Circles", "artist": "Post Malone", "duration": "3:35", "cover": "🔵"},
    {"title": "Sunflower", "artist": "Post Malone & Swae Lee", "duration": "2:38", "cover": "🌻"},
    {"title": "Shallow", "artist": "Lady Gaga & Bradley Cooper", "duration": "3:35", "cover": "🌊"},
]


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

    # Генерация mock-треков
    count = random.randint(5, 8)
    mock_tracks = random.sample(MOCK_TRACKS, k=min(count, len(MOCK_TRACKS)))

    title = data.title or f"Плейлист: {data.prompt[:40]}"

    # Сохранение в PostgreSQL
    playlist_entity = Playlist(
        title=title,
        prompt=data.prompt,
        user_id=user_id,
    )
    track_entities = [
        Track(title=t["title"], artist=t["artist"])
        for t in mock_tracks
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
                "title": t["title"],
                "artist": t["artist"],
                "duration": t["duration"],
                "cover": t["cover"],
            }
            for t in mock_tracks
        ],
        "created_at": saved_playlist.created_at.isoformat(),
    }


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
                        "duration": "",
                        "cover": "🎵",
                    }
                    for t in p.tracks
                ],
                "created_at": p.created_at.isoformat(),
            }
            for p in user_playlists
        ]
    }
