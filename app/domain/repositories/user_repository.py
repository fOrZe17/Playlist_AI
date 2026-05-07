from abc import ABC, abstractmethod

from app.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def update_password(self, user_id: int, hashed_password: str) -> User | None:
        ...

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        ...
