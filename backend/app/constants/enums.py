"""
Role enum for RBAC.
"""

from enum import Enum


class UserRole(str, Enum):
    student = "student"
    ta = "ta"
    admin = "admin"
