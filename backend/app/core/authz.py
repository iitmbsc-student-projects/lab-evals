"""
Per-session authorization helpers.

Each helper accepts an open ``db: Session`` and does NOT open or
close its own session — the caller is responsible for session
lifecycle, consistent with the rest of the codebase.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.constants.enums import SubjectRole
from app.models.lab_session import LabSession
from app.models.session_assignment import SessionAssignment


def assignment_for(
    db: Session, user_id: int, lab_session_id: int
) -> SessionAssignment | None:
    """Return the SessionAssignment for (user, session), or None."""
    return (
        db.query(SessionAssignment)
        .filter_by(user_id=user_id, lab_session_id=lab_session_id)
        .first()
    )


def is_ta_on_session(db: Session, user_id: int, lab_session_id: int) -> bool:
    """Return True if the user is assigned as TA on the given session."""
    assignment = assignment_for(db, user_id, lab_session_id)
    return assignment is not None and assignment.role == SubjectRole.ta


def is_student_on_session(
    db: Session, user_id: int, lab_session_id: int
) -> bool:
    """Return True if the user is assigned as student on the given session."""
    assignment = assignment_for(db, user_id, lab_session_id)
    return assignment is not None and assignment.role == SubjectRole.student


def get_session_or_404(db: Session, lab_session_id: int) -> LabSession:
    """Return the LabSession or raise HTTP 404."""
    session = db.query(LabSession).filter_by(id=lab_session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab session not found",
        )
    return session
