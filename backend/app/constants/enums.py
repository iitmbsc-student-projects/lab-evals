"""
Role enum for per-subject RBAC.
"""

from enum import Enum


class SubjectRole(str, Enum):
    student = "student"
    ta = "ta"
