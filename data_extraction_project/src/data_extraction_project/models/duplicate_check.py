import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import CreatedOnlyMixin, UUIDPKMixin


class DuplicateCheck(UUIDPKMixin, CreatedOnlyMixin, Base):
    __tablename__ = "duplicate_checks"

    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    matched_expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    match_type: Mapped[str] = mapped_column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint("expense_id <> matched_expense_id", name="not_self_match"),
        Index("ix_duplicate_checks_expense_id", "expense_id"),
        Index("ix_duplicate_checks_matched_expense_id", "matched_expense_id"),
    )
