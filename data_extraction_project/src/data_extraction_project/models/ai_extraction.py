import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import CreatedOnlyMixin, UUIDPKMixin


class AIExtraction(UUIDPKMixin, CreatedOnlyMixin, Base):
    __tablename__ = "ai_extractions"

    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False
    )
    merchant: Mapped[str | None] = mapped_column(String(255))
    merchant_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    amount_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    date: Mapped[dt.date | None] = mapped_column(Date)
    date_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    category_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    # [{"text": ..., "price": ..., "is_alcohol": ..., "reason": ...}, ...]
    line_items: Mapped[list | None] = mapped_column(JSONB)

    __table_args__ = (
        Index("ix_ai_extractions_receipt_id", "receipt_id"),
        Index("ix_ai_extractions_category_id", "category_id"),
    )
