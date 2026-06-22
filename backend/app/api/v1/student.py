"""
Student endpoints for read-only session access.
Authorization is per-endpoint: caller must be assigned as student
on the referenced lab session.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.authz import get_session_or_404, is_student_on_session
from app.core.database import SessionLocal
from app.models.evaluation import Evaluation
from app.models.question import Question
from app.models.user import User
from app.schemas.evaluation import StudentEvaluationResponse
from app.schemas.question import QuestionResponse

router = APIRouter()


# --- List questions for a session's subject ---


@router.get(
    "/sessions/{lab_session_id}/questions",
    response_model=list[QuestionResponse],
)
def list_questions(
    lab_session_id: int,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        if not is_student_on_session(db, current_user.id, lab_session_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a student on this session",
            )
        lab_session = get_session_or_404(db, lab_session_id)
        return (
            db.query(Question)
            .filter(Question.subject_id == lab_session.subject_id)
            .all()
        )
    finally:
        db.close()


# --- List own evaluations for a session (presence-only; no marks) ---


@router.get(
    "/sessions/{lab_session_id}/evaluations",
    response_model=list[StudentEvaluationResponse],
)
def list_evaluations(
    lab_session_id: int,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        if not is_student_on_session(db, current_user.id, lab_session_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a student on this session",
            )
        return (
            db.query(Evaluation)
            .filter(
                Evaluation.lab_session_id == lab_session_id,
                Evaluation.student_id == current_user.id,
            )
            .all()
        )
    finally:
        db.close()
