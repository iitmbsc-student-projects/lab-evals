"""
Subject model. Created by admin. Has many questions and lab sessions.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    questions = relationship(
        "Question", back_populates="subject", cascade="all, delete-orphan"
    )
    lab_sessions = relationship(
        "LabSession",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
