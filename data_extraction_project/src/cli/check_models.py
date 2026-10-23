# Verifies every table's audit columns against the agreed matrix, and prints the DDL.

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateIndex, CreateTable

import data_extraction_project.models  # noqa: F401
from data_extraction_project.db.postgres_db import Base

FULL = {"created_at", "created_by", "updated_at", "updated_by", "is_active", "is_deleted"}
AUDIT = FULL | set()
TS = {"created_at", "updated_at"}
CREATED = {"created_at"}
EXPENSE = {"created_at", "updated_at", "updated_by", "is_deleted"}

EXPECTED = {
    "users": FULL, "claims": FULL, "categories": FULL, "receipts": FULL,
    "expenses": EXPENSE,
    "receipt_processing_jobs": TS,
    "ai_extractions": CREATED, "duplicate_checks": CREATED, "recommendations": CREATED,
}
AUDIT_COLS = FULL


def main() -> None:
    configure_mappers()
    ok = True
    for name, expected in EXPECTED.items():
        cols = {c.name for c in Base.metadata.tables[name].columns}
        actual = cols & AUDIT_COLS
        status = "OK " if actual == expected else "BAD"
        if actual != expected:
            ok = False
            print(f"{status} {name}: expected {sorted(expected)} got {sorted(actual)}")
        else:
            print(f"{status} {name}: {sorted(actual)}")
    assert set(EXPECTED) == set(Base.metadata.tables), "table list drifted from matrix"
    d = postgresql.dialect()
    for t in Base.metadata.sorted_tables:
        print(CreateTable(t).compile(dialect=d))
        for ix in t.indexes:
            print(CreateIndex(ix).compile(dialect=d))
    print("MATRIX MATCH" if ok else "MATRIX MISMATCH")


if __name__ == "__main__":
    main()
