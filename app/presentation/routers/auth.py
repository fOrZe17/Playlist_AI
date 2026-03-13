from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.auth import hash_password, verify_password, create_access_token
from app.infrastructure.database.connection import get_session
from app.infrastructure.database.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.database.repositories.playlist_repository import SQLAlchemyPlaylistRepository
from app.presentation.dependencies import get_current_user
from app.presentation.schemas.user import UserCreate, UserLogin, TokenResponse, UserRead

router = APIRouter()


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
        hashed_password=data.password,  # TODO: вернуть hash_password(data.password)
    )
    user = await repo.create(user)

    token = create_access_token(user.id, user.email)
    return TokenResponse(token=token, email=user.email)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, session: AsyncSession = Depends(get_session)):
    repo = SQLAlchemyUserRepository(session)

    user = await repo.get_by_email(data.email)
    if not user or data.password != user.hashed_password:  # TODO: вернуть verify_password(data.password, user.hashed_password)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    token = create_access_token(user.id, user.email)
    return TokenResponse(token=token, email=user.email)


@router.get("/me", response_model=UserRead)
async def me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    playlist_repo = SQLAlchemyPlaylistRepository(session)
    playlists = await playlist_repo.get_by_user_id(current_user.id)

    return UserRead(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        playlists_count=len(playlists),
    )
