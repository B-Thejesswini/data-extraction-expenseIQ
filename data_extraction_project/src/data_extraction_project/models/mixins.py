import datetime as dt
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.core.context import get_current_user_id


# --------------------------------------------------------------------------- #
# Atomic mixins (one concern each)
# --------------------------------------------------------------------------- #
class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class CreatedAtMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UpdatedAtMixin:
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CreatedByMixin:
    # NULL for automated writes (workers, AI pipeline, self-registration)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        default=get_current_user_id,
    )


class UpdatedByMixin:
    # Also filled on insert, so "last touched by" is never empty for human writes
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        default=get_current_user_id,
        onupdate=get_current_user_id,
    )


class IsActiveMixin:
    # business-level on/off toggle
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )


class IsDeletedMixin:
    # soft delete flag
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )


# --------------------------------------------------------------------------- #
# Named combinations (what models inherit)
# --------------------------------------------------------------------------- #
class CreatedOnlyMixin(CreatedAtMixin):
    """created_at"""


class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    """created_at, updated_at"""


class FullAuditMixin(
    TimestampMixin, CreatedByMixin, UpdatedByMixin, IsActiveMixin, IsDeletedMixin
):
    """created_at, created_by, updated_at, updated_by, is_active, is_deleted"""
