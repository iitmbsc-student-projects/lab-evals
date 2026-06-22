"""
Evaluation model.
Created by TA for a student within a lab session.
Contains a 1-5 rating and remarks for a specific question.
"""

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint(
            "marking >= 1 AND marking <= 5", name="ck_evaluations_marking_1_5"
        ),
        UniqueConstraint(
            "lab_session_id",
            "student_id",
            "question_id",
            name="uq_eval_session_student_question",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    lab_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lab_sessions.id"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id"), nullable=False
    )
    ta_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    marking: Mapped[int] = mapped_column(Integer, nullable=False)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)

    lab_session = relationship("LabSession", back_populates="evaluations")
    student = relationship("User", foreign_keys=[student_id])
    ta = relationship("User", foreign_keys=[ta_id])
    question = relationship("Question")
