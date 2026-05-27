"""
Model package — eager imports ensure all models register against
``Base.metadata`` so ``create_all`` picks them up on startup.
"""

from app.models.audit_log import AuditLog

__all__ = ["AuditLog"]
