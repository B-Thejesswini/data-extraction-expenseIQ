import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import CreatedOnlyMixin, UUIDPKMixin


class Recommendation(UUIDPKMixin, CreatedOnlyMixin, Base):
    __tablename__ = "recommendations"

    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_recommendations_expense_id", "expense_id"),)
