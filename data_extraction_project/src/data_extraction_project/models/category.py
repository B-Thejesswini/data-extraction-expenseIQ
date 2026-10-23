from sqlalchemy import Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from data_extraction_project.db.postgres_db import Base
from data_extraction_project.models.mixins import FullAuditMixin, UUIDPKMixin


class Category(UUIDPKMixin, FullAuditMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (
        Index(
            "uq_categories_name_active",
            "name",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )
