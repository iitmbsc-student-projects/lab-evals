"""
User endpoints. Accessible to any authenticated user.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.database import SessionLocal
from app.models.lab_session import LabSession
from app.models.session_assignment import SessionAssignment
from app.models.subject import Subject
from app.models.user import User
from app.schemas.session_assignment import MySessionResponse
from app.schemas.user import UserResponse

router = APIRouter()


# --- Get own user info ---


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# --- List sessions the current user is assigned to ---


@router.get("/me/sessions", response_model=list[MySessionResponse])
def get_my_sessions(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = (
            db.query(SessionAssignment, LabSession, Subject)
            .join(
                LabSession,
                SessionAssignment.lab_session_id == LabSession.id,
            )
            .join(Subject, LabSession.subject_id == Subject.id)
            .filter(SessionAssignment.user_id == current_user.id)
            .order_by(LabSession.date)
            .all()
        )
        return [
            MySessionResponse(
                lab_session_id=assignment.lab_session_id,
                subject_id=lab_session.subject_id,
                subject_name=subject.name,
                date=lab_session.date,
                role=assignment.role,
                accepting_evaluations=lab_session.accepting_evaluations,
            )
            for assignment, lab_session, subject in rows
        ]
    finally:
        db.close()
