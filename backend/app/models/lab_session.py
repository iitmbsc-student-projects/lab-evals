"""
LabSession model. Represents a single lab evaluation session
for a subject on a given date. Controls whether evaluations
are open via ``accepting_evaluations``.
"""

from sqlalchemy import Boolean, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LabSession(Base):
    __tablename__ = "lab_sessions"
    __table_args__ = (
        UniqueConstraint(
            "subject_id", "date", name="uq_lab_sessions_subject_date"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id"), nullable=False
    )
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    accepting_evaluations: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    subject = relationship("Subject", back_populates="lab_sessions")
    assignments = relationship(
        "SessionAssignment",
        back_populates="lab_session",
        cascade="all, delete-orphan",
    )
    evaluations = relationship(
        "Evaluation",
        back_populates="lab_session",
        cascade="all, delete-orphan",
    )
