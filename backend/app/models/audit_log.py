"""
AuditLog model — append-only record of mutating actions.

All actor fields are denormalized by design (no FKs) so audit rows survive
deletion of both the actor and the target resource. JSON columns
map to JSONB on PostgreSQL and TEXT on SQLite automatically.
"""

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_created_at", "created_at"),
        Index("ix_audit_log_actor_created", "actor_user_id", "created_at"),
        Index(
            "ix_audit_log_resource",
            "resource_type",
            "resource_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(16), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    http_method: Mapped[str] = mapped_column(String(8), nullable=False)
    http_path: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_body: Mapped[dict | list | None] = mapped_column(
        JSON(none_as_null=True), nullable=True
    )
    before_state: Mapped[dict | list | None] = mapped_column(
        JSON(none_as_null=True), nullable=True
    )
    after_state: Mapped[dict | list | None] = mapped_column(
        JSON(none_as_null=True), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
