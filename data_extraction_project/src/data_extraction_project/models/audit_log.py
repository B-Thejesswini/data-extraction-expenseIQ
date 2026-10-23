import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import CreatedOnlyMixin, UUIDPKMixin


class AuditLog(UUIDPKMixin, CreatedOnlyMixin, Base):
    """Append-only change history: one row per changed field."""

    __tablename__ = "audit_logs"

    # NULL when the change was made by the system / AI pipeline (no logged-in user)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # polymorphic reference (claims, expenses, ...), so deliberately no FK
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_audit_log_entity", "entity_type", "entity_id"),
        Index("ix_audit_log_actor_id", "actor_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )
