"""
Model package — eager imports ensure all models register against
``Base.metadata`` so ``create_all`` picks them up on startup.
"""

from app.models.audit_log import AuditLog
from app.models.evaluation import Evaluation
from app.models.lab_session import LabSession
from app.models.question import Question
from app.models.session_assignment import SessionAssignment
from app.models.subject import Subject
from app.models.user import User

__all__ = [
    "AuditLog",
    "Evaluation",
    "LabSession",
    "Question",
    "SessionAssignment",
    "Subject",
    "User",
]
