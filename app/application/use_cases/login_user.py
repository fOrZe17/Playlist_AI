from app.domain.entities.user import User
from app.domain.exceptions import InvalidCredentials, UserNotFound
from app.domain.repositories.user_repository import UserRepository


class LoginUser:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def execute(self, email: str, password: str) -> User:
        """Авторизация пользователя. TODO: реализовать проверку пароля и выдачу токена."""
        user = await self._user_repo.get_by_email(email)
        if not user:
            raise UserNotFound(f"Пользователь с email {email} не найден")

        # TODO: проверка password vs user.hashed_password через passlib
        return user
