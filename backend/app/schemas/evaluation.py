"""
Pydantic schemas for Evaluation model.
"""

from pydantic import BaseModel, Field


class EvaluationBase(BaseModel):
    lab_session_id: int
    student_id: int
    question_id: int
    ta_id: int
    marking: int = Field(ge=1, le=5)
    remarks: str | None = None

    class Config:
        extra = "forbid"


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationUpdate(EvaluationBase):
    pass


class EvaluationResponse(EvaluationBase):
    id: int

    class Config:
        from_attributes = True
        extra = "forbid"


class StudentEvaluationResponse(BaseModel):
    id: int
    lab_session_id: int
    student_id: int
    question_id: int
    ta_id: int

    class Config:
        from_attributes = True
        extra = "forbid"


class TAEvaluationBase(BaseModel):
    lab_session_id: int
    student_id: int
    question_id: int
    marking: int = Field(ge=1, le=5)
    remarks: str | None = None


class TAEvaluationCreate(TAEvaluationBase):
    pass


class TAEvaluationUpdate(BaseModel):
    marking: int = Field(ge=1, le=5)
    remarks: str | None = None

    class Config:
        extra = "forbid"


class TAEvaluationResponse(TAEvaluationBase):
    id: int
    ta_id: int

    class Config:
        from_attributes = True
        extra = "forbid"
