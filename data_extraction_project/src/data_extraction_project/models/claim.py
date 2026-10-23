import datetime as dt
import uuid

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import FullAuditMixin, UUIDPKMixin


class Claim(UUIDPKMixin, FullAuditMixin, Base):
    __tablename__ = "claims"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    claim_title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    from_date: Mapped[dt.date | None] = mapped_column(Date)
    to_date: Mapped[dt.date | None] = mapped_column(Date)
    current_status: Mapped[str] = mapped_column(String(30), nullable=False)
    recommendation: Mapped[str | None] = mapped_column(String(30))

    __table_args__ = (
        Index("ix_claims_user_id", "user_id"),
        Index("ix_claims_current_status", "current_status"),
    )
