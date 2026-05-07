from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models.user import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.get(UserModel, user_id)
        return self._to_entity(result) if result else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            hashed_password=user.hashed_password,
            display_name=user.display_name,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
            show_email=user.show_email,
            show_created_at=user.show_created_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update_profile(
        self,
        user_id: int,
        display_name: str,
        first_name: str | None = None,
        last_name: str | None = None,
        show_email: bool = True,
        show_created_at: bool = True,
        avatar_url: str | None = None,
    ) -> User | None:
        model = await self._session.get(UserModel, user_id)
        if not model:
            return None

        model.display_name = display_name
        model.first_name = first_name
        model.last_name = last_name
        model.show_email = show_email
        model.show_created_at = show_created_at
        if avatar_url is not None:
            model.avatar_url = avatar_url

        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update_password(self, user_id: int, hashed_password: str) -> User | None:
        model = await self._session.get(UserModel, user_id)
        if not model:
            return None

        model.hashed_password = hashed_password
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, user_id: int) -> None:
        model = await self._session.get(UserModel, user_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            display_name=model.display_name,
            first_name=model.first_name,
            last_name=model.last_name,
            avatar_url=model.avatar_url,
            show_email=model.show_email,
            show_created_at=model.show_created_at,
            created_at=model.created_at,
        )
