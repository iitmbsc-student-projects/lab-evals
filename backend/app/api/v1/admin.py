"""
Admin endpoints for managing subjects, questions, lab sessions,
session assignments, users, evaluations, and audit export.
RBAC: Admin only.
"""

import csv
import io
import json
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import require_admin
from app.constants.enums import SubjectRole
from app.core.audit import AuditRecorder, get_audit_recorder, snapshot
from app.core.database import SessionLocal
from app.models.audit_log import AuditLog
from app.models.evaluation import Evaluation
from app.models.lab_session import LabSession
from app.models.question import Question
from app.models.session_assignment import SessionAssignment
from app.models.subject import Subject
from app.models.user import User
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationUpdate,
)
from app.schemas.lab_session import (
    LabSessionCreate,
    LabSessionResponse,
    LabSessionUpdate,
)
from app.schemas.question import (
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
)
from app.schemas.session_assignment import (
    SessionAssignmentCreate,
    SessionAssignmentResponse,
)
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(dependencies=[Depends(require_admin)])


# --- Subject Endpoints ---


@router.post("/subjects", response_model=SubjectResponse)
def create_subject(
    subject: SubjectCreate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = Subject(name=subject.name, description=subject.description)
        db.add(db_obj)
        db.flush()
        audit.record(
            db,
            action="subject.create",
            resource_type="subject",
            resource_id=db_obj.id,
            request_body=subject.model_dump(),
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: int):
    db = SessionLocal()
    try:
        db_obj = db.query(Subject).filter_by(id=subject_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )
        return db_obj
    finally:
        db.close()


@router.get("/subjects", response_model=list[SubjectResponse])
def list_subjects():
    db = SessionLocal()
    try:
        return db.query(Subject).all()
    finally:
        db.close()


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    subject: SubjectUpdate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(Subject).filter_by(id=subject_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )
        before = snapshot(db_obj)
        db_obj.name = subject.name
        if subject.description is not None:
            db_obj.description = subject.description
        audit.record(
            db,
            action="subject.update",
            resource_type="subject",
            resource_id=db_obj.id,
            request_body=subject.model_dump(),
            before_state=before,
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.delete("/subjects/{subject_id}")
def delete_subject(
    subject_id: int,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(Subject).filter_by(id=subject_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found",
            )
        before = snapshot(db_obj)
        db.delete(db_obj)
        audit.record(
            db,
            action="subject.delete",
            resource_type="subject",
            resource_id=subject_id,
            before_state=before,
            actor_role="admin",
        )
        db.commit()
        return {}, status.HTTP_204_NO_CONTENT
    finally:
        db.close()


# --- Question Endpoints ---


@router.post("/questions", response_model=QuestionResponse)
def create_question(
    question: QuestionCreate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter_by(id=question.subject_id).first()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject does not exist",
            )
        db_obj = Question(subject_id=question.subject_id, text=question.text)
        db.add(db_obj)
        db.flush()
        audit.record(
            db,
            action="question.create",
            resource_type="question",
            resource_id=db_obj.id,
            request_body=question.model_dump(),
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.get("/questions/{question_id}", response_model=QuestionResponse)
def get_question(question_id: int):
    db = SessionLocal()
    try:
        db_obj = db.query(Question).filter_by(id=question_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )
        return db_obj
    finally:
        db.close()


@router.get("/questions", response_model=list[QuestionResponse])
def list_questions():
    db = SessionLocal()
    try:
        return db.query(Question).all()
    finally:
        db.close()


@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    question: QuestionUpdate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(Question).filter_by(id=question_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )
        subject = db.query(Subject).filter_by(id=question.subject_id).first()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject does not exist",
            )
        before = snapshot(db_obj)
        db_obj.subject_id = question.subject_id
        db_obj.text = question.text
        audit.record(
            db,
            action="question.update",
            resource_type="question",
            resource_id=db_obj.id,
            request_body=question.model_dump(),
            before_state=before,
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(Question).filter_by(id=question_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )
        before = snapshot(db_obj)
        db.delete(db_obj)
        audit.record(
            db,
            action="question.delete",
            resource_type="question",
            resource_id=question_id,
            before_state=before,
            actor_role="admin",
        )
        db.commit()
        return {}, status.HTTP_204_NO_CONTENT
    finally:
        db.close()


# --- User Endpoints ---


@router.post("/users", response_model=UserResponse)
def create_user(
    user: UserCreate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = User(
            name=user.name,
            email=user.email,
            google_sub=user.google_sub,
            is_admin=user.is_admin,
        )
        db.add(db_obj)
        db.flush()
        audit.record(
            db,
            action="user.create",
            resource_type="user",
            resource_id=db_obj.id,
            request_body=user.model_dump(),
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    db = SessionLocal()
    try:
        db_obj = db.query(User).filter_by(id=user_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return db_obj
    finally:
        db.close()


@router.get("/users", response_model=list[UserResponse])
def list_users():
    db = SessionLocal()
    try:
        return db.query(User).all()
    finally:
        db.close()


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(User).filter_by(id=user_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        before = snapshot(db_obj)
        db_obj.name = user.name
        db_obj.email = user.email
        if user.google_sub is not None:
            db_obj.google_sub = user.google_sub
        db_obj.is_admin = user.is_admin
        audit.record(
            db,
            action="user.update",
            resource_type="user",
            resource_id=db_obj.id,
            request_body=user.model_dump(),
            before_state=before,
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(User).filter_by(id=user_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        before = snapshot(db_obj)
        db.delete(db_obj)
        audit.record(
            db,
            action="user.delete",
            resource_type="user",
            resource_id=user_id,
            before_state=before,
            actor_role="admin",
        )
        db.commit()
        return {}, status.HTTP_204_NO_CONTENT
    finally:
        db.close()


# --- Lab Session Endpoints ---


@router.post("/lab-sessions", response_model=LabSessionResponse)
def create_lab_session(
    session: LabSessionCreate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        subject = db.query(Subject).filter_by(id=session.subject_id).first()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subject does not exist",
            )
        exists = (
            db.query(LabSession)
            .filter_by(
                subject_id=session.subject_id,
                date=session.date,
            )
            .first()
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Lab session already exists for this subject and date"
                ),
            )
        db_obj = LabSession(
            subject_id=session.subject_id,
            date=session.date,
            accepting_evaluations=session.accepting_evaluations,
        )
        db.add(db_obj)
        db.flush()
        audit.record(
            db,
            action="lab_session.create",
            resource_type="lab_session",
            resource_id=db_obj.id,
            request_body=session.model_dump(),
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.get("/lab-sessions/{session_id}", response_model=LabSessionResponse)
def get_lab_session(session_id: int):
    db = SessionLocal()
    try:
        db_obj = db.query(LabSession).filter_by(id=session_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lab session not found",
            )
        return db_obj
    finally:
        db.close()


@router.get("/lab-sessions", response_model=list[LabSessionResponse])
def list_lab_sessions(subject_id: int | None = None):
    db = SessionLocal()
    try:
        query = db.query(LabSession)
        if subject_id is not None:
            query = query.filter_by(subject_id=subject_id)
        return query.all()
    finally:
        db.close()


@router.put("/lab-sessions/{session_id}", response_model=LabSessionResponse)
def update_lab_session(
    session_id: int,
    session: LabSessionUpdate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(LabSession).filter_by(id=session_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lab session not found",
            )
        before = snapshot(db_obj)
        db_obj.date = session.date
        db_obj.accepting_evaluations = session.accepting_evaluations
        audit.record(
            db,
            action="lab_session.update",
            resource_type="lab_session",
            resource_id=db_obj.id,
            request_body=session.model_dump(),
            before_state=before,
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.delete("/lab-sessions/{session_id}")
def delete_lab_session(
    session_id: int,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(LabSession).filter_by(id=session_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lab session not found",
            )
        before = snapshot(db_obj)
        db.delete(db_obj)
        audit.record(
            db,
            action="lab_session.delete",
            resource_type="lab_session",
            resource_id=session_id,
            before_state=before,
            actor_role="admin",
        )
        db.commit()
        return {}, status.HTTP_204_NO_CONTENT
    finally:
        db.close()


@router.patch(
    "/lab-sessions/{session_id}/accepting",
    response_model=LabSessionResponse,
)
def set_lab_session_accepting(
    session_id: int,
    accepting_evaluations: bool,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(LabSession).filter_by(id=session_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lab session not found",
            )
        before = snapshot(db_obj)
        db_obj.accepting_evaluations = accepting_evaluations
        audit.record(
            db,
            action="lab_session.update",
            resource_type="lab_session",
            resource_id=db_obj.id,
            request_body={"accepting_evaluations": accepting_evaluations},
            before_state=before,
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


# --- Session Assignment Endpoints ---


@router.post("/session-assignments", response_model=SessionAssignmentResponse)
def create_session_assignment(
    assignment: SessionAssignmentCreate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        session = (
            db.query(LabSession)
            .filter_by(id=assignment.lab_session_id)
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lab session does not exist",
            )
        user = db.query(User).filter_by(id=assignment.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not exist",
            )
        exists = (
            db.query(SessionAssignment)
            .filter_by(
                lab_session_id=assignment.lab_session_id,
                user_id=assignment.user_id,
            )
            .first()
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment already exists for this user and session",
            )
        db_obj = SessionAssignment(
            lab_session_id=assignment.lab_session_id,
            user_id=assignment.user_id,
            role=assignment.role,
        )
        db.add(db_obj)
        db.flush()
        audit.record(
            db,
            action="session_assignment.create",
            resource_type="session_assignment",
            resource_id=db_obj.id,
            request_body=assignment.model_dump(),
            after_state=snapshot(db_obj),
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.get(
    "/session-assignments/{assignment_id}",
    response_model=SessionAssignmentResponse,
)
def get_session_assignment(assignment_id: int):
    db = SessionLocal()
    try:
        db_obj = (
            db.query(SessionAssignment).filter_by(id=assignment_id).first()
        )
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session assignment not found",
            )
        return db_obj
    finally:
        db.close()


@router.get(
    "/session-assignments",
    response_model=list[SessionAssignmentResponse],
)
def list_session_assignments(lab_session_id: int | None = None):
    db = SessionLocal()
    try:
        query = db.query(SessionAssignment)
        if lab_session_id is not None:
            query = query.filter_by(lab_session_id=lab_session_id)
        return query.all()
    finally:
        db.close()


@router.delete("/session-assignments/{assignment_id}")
def delete_session_assignment(
    assignment_id: int,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = (
            db.query(SessionAssignment).filter_by(id=assignment_id).first()
        )
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session assignment not found",
            )
        before = snapshot(db_obj)
        db.delete(db_obj)
        audit.record(
            db,
            action="session_assignment.delete",
            resource_type="session_assignment",
            resource_id=assignment_id,
            before_state=before,
            actor_role="admin",
        )
        db.commit()
        return {}, status.HTTP_204_NO_CONTENT
    finally:
        db.close()


# --- Evaluation Oversight Endpoints ---


@router.get("/evaluations", response_model=list[EvaluationResponse])
def list_evaluations():
    db = SessionLocal()
    try:
        return db.query(Evaluation).all()
    finally:
        db.close()


@router.post("/evaluations/", response_model=EvaluationResponse)
def create_evaluation(
    evaluation: EvaluationCreate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        session = (
            db.query(LabSession)
            .filter_by(id=evaluation.lab_session_id)
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lab session does not exist",
            )
        question = (
            db.query(Question).filter_by(id=evaluation.question_id).first()
        )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question does not exist",
            )
        if question.subject_id != session.subject_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Question does not belong to the session's subject"),
            )
        student_assignment = (
            db.query(SessionAssignment)
            .filter_by(
                lab_session_id=evaluation.lab_session_id,
                user_id=evaluation.student_id,
                role=SubjectRole.student,
            )
            .first()
        )
        if not student_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Student is not assigned to this session as a student"
                ),
            )
        ta_assignment = (
            db.query(SessionAssignment)
            .filter_by(
                lab_session_id=evaluation.lab_session_id,
                user_id=evaluation.ta_id,
                role=SubjectRole.ta,
            )
            .first()
        )
        if not ta_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TA is not assigned to this session as a TA",
            )
        exists = (
            db.query(Evaluation)
            .filter_by(
                lab_session_id=evaluation.lab_session_id,
                student_id=evaluation.student_id,
                question_id=evaluation.question_id,
            )
            .first()
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evaluation already exists for this data",
            )
        db_obj = Evaluation(
            lab_session_id=evaluation.lab_session_id,
            student_id=evaluation.student_id,
            question_id=evaluation.question_id,
            ta_id=evaluation.ta_id,
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
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.put("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def update_evaluation(
    evaluation_id: int,
    evaluation: EvaluationUpdate,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found",
            )
        session = (
            db.query(LabSession)
            .filter_by(id=evaluation.lab_session_id)
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lab session does not exist",
            )
        question = (
            db.query(Question).filter_by(id=evaluation.question_id).first()
        )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question does not exist",
            )
        if question.subject_id != session.subject_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Question does not belong to the session's subject"),
            )
        student_assignment = (
            db.query(SessionAssignment)
            .filter_by(
                lab_session_id=evaluation.lab_session_id,
                user_id=evaluation.student_id,
                role=SubjectRole.student,
            )
            .first()
        )
        if not student_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Student is not assigned to this session as a student"
                ),
            )
        ta_assignment = (
            db.query(SessionAssignment)
            .filter_by(
                lab_session_id=evaluation.lab_session_id,
                user_id=evaluation.ta_id,
                role=SubjectRole.ta,
            )
            .first()
        )
        if not ta_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TA is not assigned to this session as a TA",
            )
        before = snapshot(db_obj)
        db_obj.lab_session_id = evaluation.lab_session_id
        db_obj.student_id = evaluation.student_id
        db_obj.question_id = evaluation.question_id
        db_obj.ta_id = evaluation.ta_id
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
            actor_role="admin",
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


@router.delete("/evaluations/{evaluation_id}")
def delete_evaluation(
    evaluation_id: int,
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = db.query(Evaluation).filter_by(id=evaluation_id).first()
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found",
            )
        before = snapshot(db_obj)
        db.delete(db_obj)
        audit.record(
            db,
            action="evaluation.delete",
            resource_type="evaluation",
            resource_id=evaluation_id,
            before_state=before,
            actor_role="admin",
        )
        db.commit()
        return {}, status.HTTP_204_NO_CONTENT
    finally:
        db.close()


# --- Audit Log Export ---


_AUDIT_CSV_COLUMNS = [
    "created_at",
    "id",
    "actor_user_id",
    "actor_email",
    "actor_role",
    "action",
    "resource_type",
    "resource_id",
    "http_method",
    "http_path",
    "request_id",
    "ip_address",
    "user_agent",
    "request_body",
    "before_state",
    "after_state",
]


@router.get("/audit/export.csv")
def export_audit_csv(
    from_date: date | None = None,
    to_date: date | None = None,
    actor_user_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
):
    today = datetime.now(UTC).date()
    effective_from = (
        from_date if from_date is not None else today - timedelta(days=30)
    )
    effective_to_inclusive = to_date if to_date is not None else today
    to_dt_exclusive = effective_to_inclusive + timedelta(days=1)

    from_dt = datetime.combine(effective_from, datetime.min.time(), tzinfo=UTC)
    to_dt = datetime.combine(to_dt_exclusive, datetime.min.time(), tzinfo=UTC)

    filename = (
        f"audit_{effective_from.strftime('%Y%m%d')}_"
        f"{effective_to_inclusive.strftime('%Y%m%d')}.csv"
    )

    db = SessionLocal()

    def row_iter():
        try:
            query = (
                db.query(AuditLog)
                .filter(AuditLog.created_at >= from_dt)
                .filter(AuditLog.created_at < to_dt)
            )
            if actor_user_id is not None:
                query = query.filter(AuditLog.actor_user_id == actor_user_id)
            if action is not None:
                query = query.filter(AuditLog.action == action)
            if resource_type is not None:
                query = query.filter(AuditLog.resource_type == resource_type)
            query = query.order_by(AuditLog.id.asc())

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(_AUDIT_CSV_COLUMNS)
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

            for row in query.yield_per(500):
                writer.writerow(
                    [
                        row.created_at.isoformat() if row.created_at else "",
                        row.id,
                        row.actor_user_id
                        if row.actor_user_id is not None
                        else "",
                        row.actor_email if row.actor_email is not None else "",
                        row.actor_role if row.actor_role is not None else "",
                        row.action,
                        row.resource_type,
                        row.resource_id if row.resource_id is not None else "",
                        row.http_method,
                        row.http_path,
                        row.request_id if row.request_id is not None else "",
                        row.ip_address if row.ip_address is not None else "",
                        row.user_agent if row.user_agent is not None else "",
                        json.dumps(row.request_body, default=str)
                        if row.request_body is not None
                        else "",
                        json.dumps(row.before_state, default=str)
                        if row.before_state is not None
                        else "",
                        json.dumps(row.after_state, default=str)
                        if row.after_state is not None
                        else "",
                    ]
                )
                yield buf.getvalue()
                buf.seek(0)
                buf.truncate(0)
        finally:
            db.close()

    return StreamingResponse(
        row_iter(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
