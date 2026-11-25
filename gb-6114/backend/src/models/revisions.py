from sqlalchemy import JSON, BigInteger, Column, ForeignKey, Integer, String, Table, UniqueConstraint
from .base import metadata


revisions = Table(
    "case_revisions", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("case_id", ForeignKey("cases.id"), nullable=False, index=True),
    Column("version", Integer, nullable=False),
    Column("payload", JSON, nullable=False),
    Column("stats", JSON(none_as_null=True), nullable=True),
    Column("status", String(16), nullable=False, index=True),
    Column("failure", String(320), nullable=True),
    Column("base_version", Integer, nullable=True),
    Column("actor", String(48), nullable=False),
    Column("created_at", BigInteger, nullable=False),
    Column("finished_at", BigInteger, nullable=True),
    UniqueConstraint("case_id", "version", name="uq_case_revisions_version"),
)
