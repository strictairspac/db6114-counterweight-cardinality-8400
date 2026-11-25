from sqlalchemy import text

from src.models import audit, cases, reviews, revisions, runs, users  # Register the tables.
from src.models.base import metadata


def has_column(connection, table, column):
    if connection.dialect.name == "postgresql":
        query = text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = :table AND column_name = :column
        """)
    else:
        query = text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = :table AND column_name = :column
        """)
    return connection.execute(query, {"table": table, "column": column}).first() is not None


def upgrade(connection):
    # Version 2 versions the calibration samples: every correction lands in
    # case_revisions and cases.current_version publishes one ready revision.
    metadata.create_all(connection)
    if not has_column(connection, "cases", "current_version"):
        connection.execute(text("ALTER TABLE cases ADD COLUMN current_version INTEGER NOT NULL DEFAULT 1"))
    if not has_column(connection, "runs", "case_version"):
        connection.execute(text("ALTER TABLE runs ADD COLUMN case_version INTEGER NULL"))
    if connection.dialect.name == "postgresql":
        now = "EXTRACT(EPOCH FROM now())::bigint"
    else:
        now = "UNIX_TIMESTAMP()"
    if has_column(connection, "cases", "payload"):
        # Existing rows predate revisions: recompute their statistics before
        # they can serve again, so the worker picks them up as pending drafts.
        connection.execute(text(f"""
            INSERT INTO case_revisions
                (case_id, version, payload, stats, status, failure, base_version, actor, created_at, finished_at)
            SELECT c.id, 1, c.payload, NULL, 'computing', NULL, NULL, 'migration', {now}, NULL
            FROM cases c
            WHERE NOT EXISTS (
                SELECT 1 FROM case_revisions r WHERE r.case_id = c.id AND r.version = 1
            )
        """))
    connection.execute(text("UPDATE runs SET case_version = 1 WHERE case_version IS NULL"))
