"""
Audit helpers — AuditRecorder, snapshot(), and FastAPI dependency.

`AuditRecorder.record()` only stages an audit row via `db.add(...)`.
The caller is responsible for `db.commit()`, so the audit row shares
the transaction with the business mutation: both commit or both
roll back, ensuring no orphan audit entries.
"""

from datetime import date, datetime
from enum import Enum

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User


def snapshot(db_obj) -> dict:
    """Serialize a SQLAlchemy model row to a JSON-safe dict.

    Converts datetime/date -> ISO 8601 string and Enum -> .value.
    Other JSON-native types (str, int, bool, None, dict, list)
    pass through unchanged. Reads in-memory attribute values, so
    columns populated by ``onupdate=`` server defaults won't reflect
    the server-side value until after ``db.refresh()``. No audited
    model uses ``onupdate`` today; revisit if that changes.
    """
    result: dict = {}
    for col in db_obj.__table__.columns:
        value = getattr(db_obj, col.name)
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, Enum):
            value = value.value
        result[col.name] = value
    return result


class AuditRecorder:
    def __init__(self, request: Request, actor: User | None):
        self._request = request
        self._actor = actor

    def record(
        self,
        db: Session,
        *,
        action: str,
        resource_type: str,
        resource_id: int | None,
        request_body: dict | list | None = None,
        before_state: dict | list | None = None,
        after_state: dict | list | None = None,
        actor_role: str = "admin",
    ) -> None:
        request_id = getattr(self._request.state, "request_id", None)
        client = self._request.client
        ip_address = client.host if client is not None else None
        db.add(
            AuditLog(
                actor_user_id=(self._actor.id if self._actor else None),
                actor_email=(self._actor.email if self._actor else None),
                actor_role=actor_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                http_method=self._request.method,
                http_path=self._request.url.path,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=self._request.headers.get("user-agent"),
                request_body=request_body,
                before_state=before_state,
                after_state=after_state,
            )
        )


def get_audit_recorder(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> AuditRecorder:
    return AuditRecorder(request=request, actor=current_user)
