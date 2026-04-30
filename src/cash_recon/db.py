import sqlite3
from pathlib import Path

from cash_recon.exceptions import ReconException


def connect_to_database(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)

    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row

    return connection


def initialise_database(db_path: str) -> None:
    with connect_to_database(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS run_history (
                run_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE VIEW IF NOT EXISTS vw_open_exceptions_by_type AS
            SELECT
                exception_type,
                COUNT(*) AS exception_count
            FROM exception_queue
            WHERE status = 'OPEN'
            GROUP BY exception_type
            """
        )

        connection.execute(
            """
            CREATE VIEW IF NOT EXISTS vw_open_exceptions_by_severity AS
            SELECT
                severity,
                COUNT(*) AS exception_count
            FROM exception_queue
            WHERE status = 'OPEN'
            GROUP BY severity
            """
        )

        connection.execute(
            """
            CREATE VIEW IF NOT EXISTS vw_open_exceptions_by_age_bucket AS
            SELECT
                CASE
                    WHEN CAST(julianday('now') - julianday(created_at) AS INTEGER) <= 1
                        THEN '0-1 days'
                    WHEN CAST(julianday('now') - julianday(created_at) AS INTEGER) <= 3
                        THEN '2-3 days'
                    WHEN CAST(julianday('now') - julianday(created_at) AS INTEGER) <= 7
                        THEN '4-7 days'
                    ELSE '8+ days'
                END AS age_bucket,
                COUNT(*) AS exception_count
            FROM exception_queue
            WHERE status = 'OPEN'
            GROUP BY age_bucket
            """
        )

        connection.execute(
            """
            CREATE VIEW IF NOT EXISTS vw_run_history_by_status AS
            SELECT
                status,
                COUNT(*) AS run_count
            FROM run_history
            GROUP BY status
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS exception_queue (
                exception_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                exception_type TEXT NOT NULL,
                source_stage TEXT NOT NULL,
                severity TEXT NOT NULL,
                merchant_reference TEXT,
                settlement_batch_id TEXT,
                amount TEXT,
                status TEXT NOT NULL DEFAULT 'OPEN',
                description TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def record_run(
    db_path: str,
    run_id: str,
    status: str,
) -> None:
    allowed_statuses = {"SUCCESS", "FAILED"}

    if status not in allowed_statuses:
        raise ValueError(
            f"status must be one of {sorted(allowed_statuses)}"
        )

    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        connection.execute(
            """
            INSERT INTO run_history (
                run_id,
                status
            )
            VALUES (
                ?,
                ?
            )
            """,
            (run_id, status),
        )


def fetch_run_history(db_path: str) -> list[sqlite3.Row]:
    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                run_id,
                status,
                created_at
            FROM run_history
            ORDER BY created_at
            """
        ).fetchall()

    return rows


def persist_exceptions(
    db_path: str,
    run_id: str,
    exceptions: list[ReconException],
) -> int:
    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        for exception in exceptions:
            amount_as_text = None

            if exception.amount is not None:
                amount_as_text = str(exception.amount)

            connection.execute(
                """
                INSERT INTO exception_queue (
                    run_id,
                    exception_type,
                    source_stage,
                    severity,
                    merchant_reference,
                    settlement_batch_id,
                    amount,
                    status,
                    description
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    'OPEN',
                    ?
                )
                """,
                (
                    run_id,
                    exception.exception_type,
                    exception.source_stage,
                    exception.severity,
                    exception.merchant_reference,
                    exception.settlement_batch_id,
                    amount_as_text,
                    exception.description,
                ),
            )

    return len(exceptions)


def fetch_exception_queue(db_path: str) -> list[sqlite3.Row]:
    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                exception_id,
                run_id,
                exception_type,
                source_stage,
                severity,
                merchant_reference,
                settlement_batch_id,
                amount,
                status,
                description,
                created_at
            FROM exception_queue
            ORDER BY exception_id
            """
        ).fetchall()

    return rows


def fetch_open_exceptions_with_ageing(db_path: str) -> list[dict[str, object]]:
    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                exception_id,
                run_id,
                exception_type,
                source_stage,
                severity,
                merchant_reference,
                settlement_batch_id,
                amount,
                status,
                description,
                created_at,
                CAST(julianday('now') - julianday(created_at) AS INTEGER) AS age_days
            FROM exception_queue
            WHERE status = 'OPEN'
            ORDER BY created_at, exception_id
            """
        ).fetchall()

    aged_rows = []

    for row in rows:
        age_days = int(row["age_days"])
        aged_row = dict(row)
        aged_row["age_bucket"] = calculate_age_bucket(age_days)
        aged_rows.append(aged_row)

    return aged_rows


def calculate_age_bucket(age_days: int) -> str:
    if age_days <= 1:
        return "0-1 days"

    if age_days <= 3:
        return "2-3 days"

    if age_days <= 7:
        return "4-7 days"

    return "8+ days"

def fetch_open_exceptions_by_type(db_path: str) -> list[sqlite3.Row]:
    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                exception_type,
                exception_count
            FROM vw_open_exceptions_by_type
            ORDER BY exception_type
            """
        ).fetchall()

    return rows


def fetch_open_exceptions_by_severity(db_path: str) -> list[sqlite3.Row]:
    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                severity,
                exception_count
            FROM vw_open_exceptions_by_severity
            ORDER BY severity
            """
        ).fetchall()

    return rows


def fetch_open_exceptions_by_age_bucket(db_path: str) -> list[sqlite3.Row]:
    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                age_bucket,
                exception_count
            FROM vw_open_exceptions_by_age_bucket
            ORDER BY
                CASE age_bucket
                    WHEN '0-1 days' THEN 1
                    WHEN '2-3 days' THEN 2
                    WHEN '4-7 days' THEN 3
                    ELSE 4
                END
            """
        ).fetchall()

    return rows


def fetch_run_history_by_status(db_path: str) -> list[sqlite3.Row]:
    initialise_database(db_path)

    with connect_to_database(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                status,
                run_count
            FROM vw_run_history_by_status
            ORDER BY status
            """
        ).fetchall()

    return rows