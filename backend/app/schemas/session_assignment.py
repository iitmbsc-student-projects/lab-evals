"""
Pydantic schemas for SessionAssignment model.
"""

from datetime import date

from pydantic import BaseModel

from app.constants.enums import SubjectRole


class SessionAssignmentCreate(BaseModel):
    lab_session_id: int
    user_id: int
    role: SubjectRole

    class Config:
        extra = "forbid"


class SessionAssignmentResponse(BaseModel):
    id: int
    lab_session_id: int
    user_id: int
    role: SubjectRole

    class Config:
        from_attributes = True
        extra = "forbid"


class MySessionResponse(BaseModel):
    lab_session_id: int
    subject_id: int
    subject_name: str
    date: date
    role: SubjectRole
    accepting_evaluations: bool

    class Config:
        from_attributes = True
        extra = "forbid"
