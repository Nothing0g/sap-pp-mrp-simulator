"""Database setup for the local demonstration."""
from __future__ import annotations

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
SEED_PATH = PROJECT_ROOT / "sql" / "seed.sql"


def connect(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection, reset_demo_data: bool = False) -> bool:
    """Create schema and seed only if empty. Returns True if demo data was seeded."""
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    material_count = connection.execute("SELECT COUNT(*) FROM MARA").fetchone()[0]
    if reset_demo_data:
        for table in ("PLAF", "AFPO", "AFKO", "PLPO", "PLKO", "CRHD", "STPO", "STKO", "MARD", "MARC", "MARA"):
            connection.execute(f"DELETE FROM {table}")
        material_count = 0
    if material_count == 0:
        connection.executescript(SEED_PATH.read_text(encoding="utf-8"))
        connection.commit()
        return True
    connection.commit()
    return False
