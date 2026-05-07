from datetime import datetime

from sqlalchemy import String, DateTime, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    show_email: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
    show_created_at: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("date_trunc('second', now())"))

    playlists: Mapped[list["PlaylistModel"]] = relationship(back_populates="user")
