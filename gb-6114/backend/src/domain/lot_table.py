from contextlib import contextmanager
from uuid import uuid4

from sqlalchemy import text


@contextmanager
def inspection_table(db, calibration, inspection):
    table = f"counterweight_lot_{uuid4().hex[:12]}"
    db.execute(text(f"""
        CREATE TEMPORARY TABLE {table} (
            measurement_id INTEGER AUTO_INCREMENT PRIMARY KEY,
            phase TINYINT NOT NULL,
            mass VARCHAR(24) COLLATE utf8mb4_0900_bin NOT NULL,
            slot_band VARCHAR(24) COLLATE utf8mb4_0900_bin NOT NULL,
            INDEX phase_bands (phase, mass, slot_band)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))
    try:
        insert = text(f"INSERT INTO {table} (phase, mass, slot_band) VALUES (:phase, :mass, :slot)")
        for phase, cells in enumerate((calibration, inspection)):
            for cell in cells:
                db.execute(insert, [dict(phase=phase, mass=cell.mass, slot=cell.slot) for _ in range(cell.count)])
        yield table
    finally:
        db.execute(text(f"DROP TEMPORARY TABLE IF EXISTS {table}"))


def joint_frequencies(db, table):
    rows = db.execute(text(f"""
        SELECT mass, slot_band, COUNT(*) AS pieces
        FROM {table} WHERE phase = 0 GROUP BY mass, slot_band
    """))
    return {(row.mass, row.slot_band): row.pieces for row in rows}


def actual_count(db, table, check):
    return db.execute(text(f"""
        SELECT COUNT(*) FROM {table}
        WHERE phase = 1 AND mass = :mass AND slot_band = :slot
    """), {"mass": check.mass, "slot": check.slot}).scalar_one()
