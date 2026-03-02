from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.playlist import Playlist
from app.domain.repositories.playlist_repository import PlaylistRepository
from app.infrastructure.database.models.playlist import PlaylistModel


class SQLAlchemyPlaylistRepository(PlaylistRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, playlist_id: int) -> Playlist | None:
        result = await self._session.get(PlaylistModel, playlist_id)
        return self._to_entity(result) if result else None

    async def get_by_user_id(self, user_id: int) -> list[Playlist]:
        stmt = select(PlaylistModel).where(PlaylistModel.user_id == user_id)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, playlist: Playlist) -> Playlist:
        model = PlaylistModel(
            title=playlist.title,
            user_id=playlist.user_id,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, playlist_id: int) -> None:
        model = await self._session.get(PlaylistModel, playlist_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: PlaylistModel) -> Playlist:
        return Playlist(
            id=model.id,
            title=model.title,
            user_id=model.user_id,
            created_at=model.created_at,
        )
