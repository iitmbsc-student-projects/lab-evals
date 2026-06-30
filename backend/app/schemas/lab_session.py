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
    accepting_evaluations: bool

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
