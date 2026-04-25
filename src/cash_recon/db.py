import sqlite3
from pathlib import Path


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