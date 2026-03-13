from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.playlist import Playlist
from app.domain.entities.track import Track
from app.domain.repositories.playlist_repository import PlaylistRepository
from app.infrastructure.database.models.playlist import PlaylistModel
from app.infrastructure.database.models.track import TrackModel


class SQLAlchemyPlaylistRepository(PlaylistRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, playlist_id: int) -> Playlist | None:
        stmt = (
            select(PlaylistModel)
            .options(selectinload(PlaylistModel.tracks))
            .where(PlaylistModel.id == playlist_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user_id(self, user_id: int) -> list[Playlist]:
        stmt = (
            select(PlaylistModel)
            .options(selectinload(PlaylistModel.tracks))
            .where(PlaylistModel.user_id == user_id)
            .order_by(PlaylistModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, playlist: Playlist, tracks: list[Track] | None = None) -> Playlist:
        model = PlaylistModel(
            title=playlist.title,
            prompt=playlist.prompt,
            user_id=playlist.user_id,
        )
        if tracks:
            model.tracks = [
                TrackModel(
                    title=t.title,
                    artist=t.artist,
                    url=t.url,
                )
                for t in tracks
            ]
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model, ["tracks"])
        return self._to_entity(model)

    async def update_title(self, playlist_id: int, title: str) -> Playlist | None:
        model = await self._session.get(PlaylistModel, playlist_id)
        if not model:
            return None
        model.title = title
        await self._session.commit()
        await self._session.refresh(model, ["tracks"])
        return self._to_entity(model)

    async def delete(self, playlist_id: int) -> None:
        model = await self._session.get(PlaylistModel, playlist_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    async def delete_track(self, track_id: int) -> None:
        model = await self._session.get(TrackModel, track_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: PlaylistModel) -> Playlist:
        tracks = [
            Track(
                id=t.id,
                title=t.title,
                artist=t.artist,
                url=t.url,
                playlist_id=t.playlist_id,
            )
            for t in model.tracks
        ]
        return Playlist(
            id=model.id,
            title=model.title,
            prompt=model.prompt,
            user_id=model.user_id,
            created_at=model.created_at,
            tracks=tracks,
        )
