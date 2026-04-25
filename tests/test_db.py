import sqlite3

import pytest

from cash_recon.db import (
    fetch_run_history,
    initialise_database,
    record_run,
)


def test_initialise_database_creates_run_history_table(tmp_path):
    db_path = tmp_path / "test_recon.sqlite3"

    initialise_database(str(db_path))

    with sqlite3.connect(db_path) as connection:
        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'run_history'
            """
        ).fetchone()

    assert table is not None


def test_record_run_inserts_run_history_row(tmp_path):
    db_path = tmp_path / "test_recon.sqlite3"

    record_run(
        db_path=str(db_path),
        run_id="RUN-001",
        status="SUCCESS",
    )

    rows = fetch_run_history(str(db_path))

    assert len(rows) == 1
    assert rows[0]["run_id"] == "RUN-001"
    assert rows[0]["status"] == "SUCCESS"


def test_record_run_rejects_invalid_status(tmp_path):
    db_path = tmp_path / "test_recon.sqlite3"

    with pytest.raises(ValueError):
        record_run(
            db_path=str(db_path),
            run_id="RUN-001",
            status="BROKEN",
        )