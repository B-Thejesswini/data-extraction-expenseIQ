import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import IsDeletedMixin, TimestampMixin, UpdatedByMixin, UUIDPKMixin


class Expense(UUIDPKMixin, TimestampMixin, UpdatedByMixin, IsDeletedMixin, Base):
    __tablename__ = "expenses"

    # nullable: an expense exists before it is consolidated into a claim
    claim_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="SET NULL"), nullable=True
    )
    # nullable: "receipt required" is a policy rule, so receipt-less expenses can exist
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("receipts.id", ondelete="SET NULL"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    merchant: Mapped[str | None] = mapped_column(String(255))
    date: Mapped[dt.date | None] = mapped_column(Date)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    current_status: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_expenses_claim_id", "claim_id"),
        Index("ix_expenses_receipt_id", "receipt_id"),
        Index("ix_expenses_category_id", "category_id"),
        # supports the fuzzy duplicate lookup (merchant + date is the trigger)
        Index("ix_expenses_merchant_date", "merchant", "date"),
    )
