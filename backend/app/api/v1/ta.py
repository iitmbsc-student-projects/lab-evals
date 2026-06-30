"""
TA endpoints for session-scoped evaluation management.
Authorization is per-endpoint: caller must be assigned as TA on
the referenced lab session.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.constants.enums import SubjectRole
from app.core.audit import AuditRecorder, get_audit_recorder, snapshot
from app.core.authz import (
    get_session_or_404,
    is_ta_on_session,
)
from app.core.database import SessionLocal
from app.models.evaluation import Evaluation
from app.models.question import Question
from app.models.session_assignment import SessionAssignment
from app.models.user import User
from app.schemas.evaluation import (
    TAEvaluationCreate,
    TAEvaluationResponse,
    TAEvaluationUpdate,
)
from app.schemas.question import QuestionResponse
from app.schemas.user import UserResponse

router = APIRouter()


def _require_ta(db, user_id: int, lab_session_id: int) -> None:
    if not is_ta_on_session(db, user_id, lab_session_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a TA on this session",
        )


def _require_open(session) -> None:
    if not session.accepting_evaluations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session is not accepting evaluations",
        )


# --- List students on a session ---


@router.get(
    "/sessions/{lab_session_id}/students",
    response_model=list[UserResponse],
)
def list_students(
    lab_session_id: int,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        _require_ta(db, current_user.id, lab_session_id)
        rows = (
            db.query(User)
            .join(
                SessionAssignment,
                SessionAssignment.user_id == User.id,
            )
            .filter(
                SessionAssignment.lab_session_id == lab_session_id,
                SessionAssignment.role == SubjectRole.student,
            )
            .order_by(User.email)
            .all()
        )
        return rows
    finally:
        db.close()


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
        _require_ta(db, current_user.id, lab_session_id)
        lab_session = get_session_or_404(db, lab_session_id)
        return (
            db.query(Question)
            .filter(Question.subject_id == lab_session.subject_id)
            .all()
        )
    finally:
        db.close()


# --- List this TA's evaluations for a session ---


@router.get(
    "/sessions/{lab_session_id}/evaluations",
    response_model=list[TAEvaluationResponse],
)
def list_evaluations(
    lab_session_id: int,
    current_user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        _require_ta(db, current_user.id, lab_session_id)
        return (
            db.query(Evaluation)
            .filter(
                Evaluation.lab_session_id == lab_session_id,
                Evaluation.ta_id == current_user.id,
            )
            .all()
        )
    finally:
        db.close()


# --- Create evaluation ---


@router.post(
    "/sessions/{lab_session_id}/evaluations",
    response_model=TAEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation(
    lab_session_id: int,
    evaluation: TAEvaluationCreate,
    current_user: User = Depends(get_current_user),
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        _require_ta(db, current_user.id, lab_session_id)
        lab_session = get_session_or_404(db, lab_session_id)
        _require_open(lab_session)
        if evaluation.lab_session_id != lab_session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="lab_session_id in body does not match path",
            )
        question = (
            db.query(Question).filter_by(id=evaluation.question_id).first()
        )
        if not question or question.subject_id != lab_session.subject_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question does not belong to this session's subject",
            )
        student_assignment = (
            db.query(SessionAssignment)
            .filter_by(
                lab_session_id=lab_session_id,
                user_id=evaluation.student_id,
                role=SubjectRole.student,
            )
            .first()
        )
        if not student_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is not assigned to this session",
            )
        exists = (
            db.query(Evaluation)
            .filter_by(
                lab_session_id=lab_session_id,
                student_id=evaluation.student_id,
                question_id=evaluation.question_id,
            )
            .first()
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Evaluation already exists for this "
                    "session/student/question"
                ),
            )
        db_obj = Evaluation(
            lab_session_id=lab_session_id,
            student_id=evaluation.student_id,
            question_id=evaluation.question_id,
            ta_id=current_user.id,
            marking=evaluation.marking,
            remarks=evaluation.remarks,
        )
        db.add(db_obj)
        db.flush()
        audit.record(
            db,
            action="evaluation.create",
            resource_type="evaluation",
            resource_id=db_obj.id,
            request_body=evaluation.model_dump(),
            after_state=snapshot(db_obj),
            actor_role="ta",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


# --- Update evaluation (own row only; session must be open) ---


@router.put(
    "/sessions/{lab_session_id}/evaluations/{evaluation_id}",
    response_model=TAEvaluationResponse,
)
def update_evaluation(
    lab_session_id: int,
    evaluation_id: int,
    evaluation: TAEvaluationUpdate,
    current_user: User = Depends(get_current_user),
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        _require_ta(db, current_user.id, lab_session_id)
        lab_session = get_session_or_404(db, lab_session_id)
        _require_open(lab_session)
        db_obj = (
            db.query(Evaluation)
            .filter_by(
                id=evaluation_id,
                lab_session_id=lab_session_id,
                ta_id=current_user.id,
            )
            .first()
        )
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found or not permitted",
            )
        before = snapshot(db_obj)
        db_obj.marking = evaluation.marking
        if evaluation.remarks is not None:
            db_obj.remarks = evaluation.remarks
        audit.record(
            db,
            action="evaluation.update",
            resource_type="evaluation",
            resource_id=db_obj.id,
            request_body=evaluation.model_dump(),
            before_state=before,
            after_state=snapshot(db_obj),
            actor_role="ta",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


# --- Delete evaluation (own row only; session must be open) ---


@router.delete(
    "/sessions/{lab_session_id}/evaluations/{evaluation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_evaluation(
    lab_session_id: int,
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        _require_ta(db, current_user.id, lab_session_id)
        lab_session = get_session_or_404(db, lab_session_id)
        _require_open(lab_session)
        db_obj = (
            db.query(Evaluation)
            .filter_by(
                id=evaluation_id,
                lab_session_id=lab_session_id,
                ta_id=current_user.id,
            )
            .first()
        )
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found or not permitted",
            )
        before = snapshot(db_obj)
        db.delete(db_obj)
        audit.record(
            db,
            action="evaluation.delete",
            resource_type="evaluation",
            resource_id=evaluation_id,
            before_state=before,
            actor_role="ta",
        )
        db.commit()
    finally:
        db.close()
