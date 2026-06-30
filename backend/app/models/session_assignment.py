"""
SessionAssignment model. Roster entry linking a user to a lab session
with a per-session role (student or ta). Replaces the old Enrollment table.
"""

from sqlalchemy import Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.enums import SubjectRole
from app.core.database import Base


class SessionAssignment(Base):
    __tablename__ = "session_assignments_v2"
    __table_args__ = (
        UniqueConstraint(
            "lab_session_id",
            "user_id",
            name="uq_session_assignment_v2_user",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    lab_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lab_sessions.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users_v2.id"), nullable=False
    )
    role: Mapped[SubjectRole] = mapped_column(
        Enum(SubjectRole), nullable=False
    )

    lab_session = relationship("LabSession", back_populates="assignments")
    user = relationship("User", backref="session_assignments")
