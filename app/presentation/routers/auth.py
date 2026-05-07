from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.auth import hash_password, verify_password, create_access_token
from app.infrastructure.database.connection import get_session
from app.infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.database.repositories.playlist_repository import SQLAlchemyPlaylistRepository
from app.presentation.dependencies import get_current_user
from app.presentation.schemas.user import PasswordChangeRequest, UserCreate, UserLogin, TokenResponse, UserRead

router = APIRouter()

AVATAR_DIR = Path("app/presentation/static/uploads/avatars")
AVATAR_URL_PREFIX = "/static/uploads/avatars"
MAX_AVATAR_SIZE = 5 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _password_matches(plain_password: str, stored_password: str) -> bool:
    if plain_password == stored_password:
        return True
    try:
        return verify_password(plain_password, stored_password)
    except Exception:
        return False


async def _user_read(user: User, session: AsyncSession) -> UserRead:
    playlist_repo = SQLAlchemyPlaylistRepository(session)
    playlists = await playlist_repo.get_by_user_id(user.id)
    return UserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=user.avatar_url,
        show_email=user.show_email,
        show_created_at=user.show_created_at,
        created_at=user.created_at,
        playlists_count=len(playlists),
    )


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate, session: AsyncSession = Depends(get_session)):
    repo = SQLAlchemyUserRepository(session)

    existing = await repo.get_by_email(data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    user = await repo.create(user)

    token = create_access_token(user.id, user.email)
    return TokenResponse(
        token=token,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, session: AsyncSession = Depends(get_session)):
    repo = SQLAlchemyUserRepository(session)

    user = await repo.get_by_email(data.email)
    if not user or not _password_matches(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    token = create_access_token(user.id, user.email)
    return TokenResponse(
        token=token,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
    )


@router.get("/me", response_model=UserRead)
async def me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _user_read(current_user, session)


@router.put("/profile", response_model=UserRead)
async def update_profile(
    display_name: str = Form(...),
    first_name: str = Form(default=""),
    last_name: str = Form(default=""),
    show_email: bool = Form(default=True),
    show_created_at: bool = Form(default=True),
    avatar: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    name = display_name.strip()
    if len(name) < 2 or len(name) > 80:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя пользователя должно быть от 2 до 80 символов",
        )

    avatar_url = current_user.avatar_url
    if avatar and avatar.filename:
        suffix = ALLOWED_AVATAR_TYPES.get(avatar.content_type or "")
        if suffix is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Загрузите изображение JPG, PNG или WebP",
            )

        content = await avatar.read()
        if len(content) > MAX_AVATAR_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Фото должно быть меньше 5 МБ",
            )

        AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"user_{current_user.id}_{uuid4().hex}{suffix}"
        path = AVATAR_DIR / filename
        path.write_bytes(content)
        avatar_url = f"{AVATAR_URL_PREFIX}/{filename}"

    first_name_value = first_name.strip() or None
    last_name_value = last_name.strip() or None
    for value, label in ((first_name_value, "Имя"), (last_name_value, "Фамилия")):
        if value and len(value) > 80:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{label} должно быть не длиннее 80 символов",
            )

    repo = SQLAlchemyUserRepository(session)
    updated_user = await repo.update_profile(
        current_user.id,
        name,
        first_name_value,
        last_name_value,
        show_email,
        show_created_at,
        avatar_url,
    )
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    return await _user_read(updated_user, session)


@router.put("/password", response_model=UserRead)
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not _password_matches(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текущий пароль указан неверно",
        )
    if len(data.new_password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль должен быть не менее 4 символов",
        )

    repo = SQLAlchemyUserRepository(session)
    updated_user = await repo.update_password(current_user.id, hash_password(data.new_password))
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    return await _user_read(updated_user, session)
