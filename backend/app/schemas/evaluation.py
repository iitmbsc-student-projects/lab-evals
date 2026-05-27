"""
Pydantic schemas for Evaluation model.
"""

from pydantic import BaseModel, Field


class EvaluationBase(BaseModel):
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
    student_id: int
    question_id: int
    ta_id: int


class TAEvaluationBase(BaseModel):
    student_id: int
    question_id: int
    marking: int = Field(ge=1, le=5)
    remarks: str | None = None


class TAEvaluationCreate(TAEvaluationBase):
    pass


class TAEvaluationUpdate(TAEvaluationCreate):
    pass


class TAEvaluationResponse(TAEvaluationBase):
    id: int
    ta_id: int

    class Config:
        from_attributes = True
        extra = "forbid"
