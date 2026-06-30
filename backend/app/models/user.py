"""
User model for authentication.
No passwords stored; Google OAuth only. Admin flag replaces global role.
"""

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users_v2"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(
        String(256), unique=True, index=True, nullable=False
    )
    google_sub: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=True
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
