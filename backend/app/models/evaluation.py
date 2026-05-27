"""
Evaluation model.
Created by TA for a student and subject.
Contains a 1-5 rating, remarks, and per-question marks.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint(
            "marking >= 1 AND marking <= 5", name="ck_evaluations_marking_1_5"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
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

    student = relationship("User", foreign_keys=[student_id])
    ta = relationship("User", foreign_keys=[ta_id])
    question = relationship("Question")
