import sqlite3
from decimal import Decimal

import pytest

from cash_recon.db import (
    calculate_age_bucket,
    fetch_exception_queue,
    fetch_open_exceptions_with_ageing,
    fetch_run_history,
    initialise_database,
    persist_exceptions,
    record_run,
)
from cash_recon.exceptions import ReconException


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


def test_initialise_database_creates_exception_queue_table(tmp_path):
    db_path = tmp_path / "test_recon.sqlite3"

    initialise_database(str(db_path))

    with sqlite3.connect(db_path) as connection:
        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'exception_queue'
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


def test_persist_exceptions_inserts_exception_queue_rows(tmp_path):
    db_path = tmp_path / "test_recon.sqlite3"

    exceptions = [
        ReconException(
            exception_type="MISSING_BANK_RECEIPT",
            source_stage="PSP_TO_BANK",
            severity="HIGH",
            merchant_reference=None,
            settlement_batch_id="BATCH-20260421-001",
            amount=Decimal("37.05"),
            description="Expected PSP payout was not found in bank.",
        )
    ]

    inserted_count = persist_exceptions(
        db_path=str(db_path),
        run_id="RUN-001",
        exceptions=exceptions,
    )

    rows = fetch_exception_queue(str(db_path))

    assert inserted_count == 1
    assert len(rows) == 1
    assert rows[0]["run_id"] == "RUN-001"
    assert rows[0]["exception_type"] == "MISSING_BANK_RECEIPT"
    assert rows[0]["source_stage"] == "PSP_TO_BANK"
    assert rows[0]["severity"] == "HIGH"
    assert rows[0]["settlement_batch_id"] == "BATCH-20260421-001"
    assert rows[0]["amount"] == "37.05"
    assert rows[0]["status"] == "OPEN"


def test_calculate_age_bucket():
    assert calculate_age_bucket(0) == "0-1 days"
    assert calculate_age_bucket(1) == "0-1 days"
    assert calculate_age_bucket(2) == "2-3 days"
    assert calculate_age_bucket(3) == "2-3 days"
    assert calculate_age_bucket(4) == "4-7 days"
    assert calculate_age_bucket(7) == "4-7 days"
    assert calculate_age_bucket(8) == "8+ days"


def test_fetch_open_exceptions_with_ageing(tmp_path):
    db_path = tmp_path / "test_recon.sqlite3"

    exceptions = [
        ReconException(
            exception_type="MISSING_BANK_RECEIPT",
            source_stage="PSP_TO_BANK",
            severity="HIGH",
            merchant_reference=None,
            settlement_batch_id="BATCH-20260421-001",
            amount=Decimal("37.05"),
            description="Expected PSP payout was not found in bank.",
        )
    ]

    persist_exceptions(
        db_path=str(db_path),
        run_id="RUN-001",
        exceptions=exceptions,
    )

    rows = fetch_open_exceptions_with_ageing(str(db_path))

    assert len(rows) == 1
    assert rows[0]["run_id"] == "RUN-001"
    assert rows[0]["exception_type"] == "MISSING_BANK_RECEIPT"
    assert rows[0]["status"] == "OPEN"
    assert rows[0]["age_days"] >= 0
    assert rows[0]["age_bucket"] == "0-1 days"