"""
Pydantic schemas for SessionAssignment model.
"""

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
