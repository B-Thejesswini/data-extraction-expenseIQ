import uuid

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import FullAuditMixin, UUIDPKMixin


class User(UUIDPKMixin, FullAuditMixin, Base):
    __tablename__ = "users"

    role: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # self-referencing: the user's approving manager
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        # soft-deleted users must not block re-use of their email
        Index(
            "uq_users_email_active",
            "email",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )
