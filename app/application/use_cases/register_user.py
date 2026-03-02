from app.domain.entities.user import User
from app.domain.exceptions import UserAlreadyExists
from app.domain.repositories.user_repository import UserRepository


class RegisterUser:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def execute(self, email: str, hashed_password: str) -> User:
        """Регистрация нового пользователя. TODO: реализовать хеширование пароля."""
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise UserAlreadyExists(f"Пользователь с email {email} уже существует")

        user = User(email=email, hashed_password=hashed_password)
        return await self._user_repo.create(user)
