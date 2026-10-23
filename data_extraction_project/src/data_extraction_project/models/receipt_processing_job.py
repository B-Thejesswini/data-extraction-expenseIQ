import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import TimestampMixin, UUIDPKMixin


class ReceiptProcessingJob(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "receipt_processing_jobs"

    # groups the files of one bulk upload (no batches table; plain UUID)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False
    )
    # output of the job: NULL until the expense is created from the extraction
    expense_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    error_message: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_receipt_processing_jobs_batch_id", "batch_id"),
        Index("ix_receipt_processing_jobs_receipt_id", "receipt_id"),
        Index("ix_receipt_processing_jobs_expense_id", "expense_id"),
        # SKIP LOCKED worker only scans pending rows
        Index(
            "ix_receipt_processing_jobs_pending",
            "created_at",
            postgresql_where=text("status = 'pending'"),
        ),
    )
