from datetime import datetime

from sqlalchemy import Boolean, String, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class PlaylistModel(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(String(500), nullable=False, server_default="")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("date_trunc('second', now())"))

    user: Mapped["UserModel"] = relationship(back_populates="playlists")
    tracks: Mapped[list["TrackModel"]] = relationship(back_populates="playlist")
