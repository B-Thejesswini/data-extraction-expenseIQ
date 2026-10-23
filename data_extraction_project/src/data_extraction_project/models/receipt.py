from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import FullAuditMixin, UUIDPKMixin


class Receipt(UUIDPKMixin, FullAuditMixin, Base):
    """First entity in the flow: receipt -> expense -> claim."""

    __tablename__ = "receipts"


    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    # SHA-256 hex digest; org-wide duplicate signal, so indexed but NOT unique
    # (a duplicate upload must still be storable so it can be flagged).
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (Index("ix_receipts_file_hash", "file_hash"),)
