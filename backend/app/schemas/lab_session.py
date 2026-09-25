"""
Pydantic schemas for LabSession model.
"""

from datetime import date

from pydantic import BaseModel


class LabSessionCreate(BaseModel):
    subject_id: int
    date: date
    accepting_evaluations: bool = False

    class Config:
        extra = "forbid"


class LabSessionUpdate(BaseModel):
    date: date
    # Optional: the admin UI edits the date only and leaves the open/closed
    # state to PATCH /lab-sessions/{id}/accepting, so a date edit made from
    # a stale row cannot silently re-open a session another admin closed.
    accepting_evaluations: bool | None = None

    class Config:
        extra = "forbid"


class LabSessionResponse(BaseModel):
    id: int
    subject_id: int
    date: date
    accepting_evaluations: bool

    class Config:
        from_attributes = True
        extra = "forbid"
