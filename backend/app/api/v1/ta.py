"""
TA endpoints for creating and updating evaluations.
RBAC: TA only.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, require_role
from app.constants.enums import UserRole
from app.core.audit import AuditRecorder, get_audit_recorder, snapshot
from app.core.database import SessionLocal
from app.models.enrollment import Enrollment
from app.models.evaluation import Evaluation
from app.models.question import Question
from app.models.subject import Subject
from app.models.user import User
from app.schemas.enrollment import EnrollmentResponse
from app.schemas.evaluation import (
    TAEvaluationCreate,
    TAEvaluationResponse,
    TAEvaluationUpdate,
)
from app.schemas.question import QuestionResponse
from app.schemas.subject import SubjectResponse
from app.schemas.user import UserResponse

router = APIRouter(dependencies=[Depends(require_role(UserRole.ta))])


# --- List students (not TAs or admins) ---


@router.get("/students", response_model=list[UserResponse])
def list_students():
    db = SessionLocal()
    try:
        return (
            db.query(User)
            .filter(User.role == UserRole.student)
            .order_by(User.email)
            .all()
        )
    finally:
        db.close()


# --- List enrollments ---


@router.get("/enrollments", response_model=list[EnrollmentResponse])
def list_enrollments():
    db = SessionLocal()
    try:
        return db.query(Enrollment).all()
    finally:
        db.close()


# --- List subjects ---


@router.get("/subjects", response_model=list[SubjectResponse])
def list_subjects():
    db = SessionLocal()
    try:
        return db.query(Subject).all()
    finally:
        db.close()


# --- List questions ---


@router.get("/questions", response_model=list[QuestionResponse])
def list_questions():
    db = SessionLocal()
    try:
        return db.query(Question).all()
    finally:
        db.close()


# --- Create evaluation ---


@router.post("/evaluations", response_model=TAEvaluationResponse)
def create_evaluation(
    evaluation: TAEvaluationCreate,
    current_user: User = Depends(get_current_user),
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        student = db.query(User).filter_by(id=evaluation.student_id).first()
        if not student or student.role != UserRole.student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid student ID",
            )
        question = (
            db.query(Question).filter_by(id=evaluation.question_id).first()
        )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid question ID",
            )
        enrollment = (
            db.query(Enrollment)
            .filter_by(
                user_id=evaluation.student_id,
                subject_id=question.subject_id,
            )
            .first()
        )
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student not enrolled in the subject of the question",
            )
        exists = (
            db.query(Evaluation)
            .filter_by(
                student_id=evaluation.student_id,
                question_id=evaluation.question_id,
                ta_id=current_user.id,
            )
            .first()
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evaluation already exists for this student - question",
            )
        db_obj = Evaluation(
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
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


# --- List evaluations made by this TA ---


@router.get("/evaluations", response_model=list[TAEvaluationResponse])
def list_evaluations(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        return (
            db.query(Evaluation)
            .filter(Evaluation.ta_id == current_user.id)
            .all()
        )
    finally:
        db.close()


# --- Get single evaluation (only if made by this TA) ---


@router.get(
    "/evaluations/{evaluation_id}", response_model=TAEvaluationResponse
)
def get_evaluation(
    evaluation_id: int, current_user: User = Depends(get_current_user)
):
    db = SessionLocal()
    try:
        db_obj = (
            db.query(Evaluation)
            .filter_by(id=evaluation_id, ta_id=current_user.id)
            .first()
        )
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found or not permitted",
            )
        return db_obj
    finally:
        db.close()


# --- Update evaluation (only if made by this TA) ---


@router.put(
    "/evaluations/{evaluation_id}", response_model=TAEvaluationResponse
)
def update_evaluation(
    evaluation_id: int,
    evaluation: TAEvaluationUpdate,
    current_user: User = Depends(get_current_user),
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = (
            db.query(Evaluation)
            .filter_by(id=evaluation_id, ta_id=current_user.id)
            .first()
        )
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found or not permitted",
            )
        before = snapshot(db_obj)
        db_obj.student_id = evaluation.student_id
        db_obj.question_id = evaluation.question_id
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
        )
        db.commit()
        db.refresh(db_obj)
        return db_obj
    finally:
        db.close()


# --- Delete evaluation (only if made by this TA) ---


@router.delete("/evaluations/{evaluation_id}")
def delete_evaluation(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    audit: AuditRecorder = Depends(get_audit_recorder),
):
    db = SessionLocal()
    try:
        db_obj = (
            db.query(Evaluation)
            .filter_by(id=evaluation_id, ta_id=current_user.id)
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
        )
        db.commit()
        return {}, status.HTTP_204_NO_CONTENT
    finally:
        db.close()
