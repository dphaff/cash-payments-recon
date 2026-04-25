import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


REQUIRED_COLUMNS = [
    "event_id",
    "event_date",
    "merchant_reference",
    "event_type",
    "gross_amount",
    "currency",
]

ALLOWED_EVENT_TYPES = {"PAYMENT", "REFUND"}
ALLOWED_CURRENCY = "GBP"


@dataclass
class InternalEvent:
    event_id: str
    event_date: date
    merchant_reference: str
    event_type: str
    gross_amount: Decimal
    currency: str


def load_internal_events(file_path: str) -> list[InternalEvent]:
    path = Path(file_path)

    if not path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    with path.open("r", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames != REQUIRED_COLUMNS:
            raise ValueError(
                f"Invalid columns. Expected {REQUIRED_COLUMNS}, got {reader.fieldnames}"
            )

        events = []

        for row_number, row in enumerate(reader, start=2):
            event = _parse_internal_event(row, row_number)
            events.append(event)

    return events


def _parse_internal_event(row: dict[str, str], row_number: int) -> InternalEvent:
    event_id = _require_value(row, "event_id", row_number)
    event_date_raw = _require_value(row, "event_date", row_number)
    merchant_reference = _require_value(row, "merchant_reference", row_number)
    event_type = _require_value(row, "event_type", row_number)
    gross_amount_raw = _require_value(row, "gross_amount", row_number)
    currency = _require_value(row, "currency", row_number)

    try:
        event_date = date.fromisoformat(event_date_raw)
    except ValueError:
        raise ValueError(
            f"Row {row_number}: event_date must use YYYY-MM-DD format"
        )

    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(
            f"Row {row_number}: event_type must be one of {sorted(ALLOWED_EVENT_TYPES)}"
        )

    try:
        gross_amount = Decimal(gross_amount_raw)
    except InvalidOperation:
        raise ValueError(
            f"Row {row_number}: gross_amount must be a valid number"
        )

    if currency != ALLOWED_CURRENCY:
        raise ValueError(
            f"Row {row_number}: currency must be {ALLOWED_CURRENCY}"
        )

    if event_type == "PAYMENT" and gross_amount <= Decimal("0.00"):
        raise ValueError(
            f"Row {row_number}: PAYMENT gross_amount must be positive"
        )

    if event_type == "REFUND" and gross_amount >= Decimal("0.00"):
        raise ValueError(
            f"Row {row_number}: REFUND gross_amount must be negative"
        )

    return InternalEvent(
        event_id=event_id,
        event_date=event_date,
        merchant_reference=merchant_reference,
        event_type=event_type,
        gross_amount=gross_amount,
        currency=currency,
    )


def _require_value(row: dict[str, str], column: str, row_number: int) -> str:
    value = row.get(column)

    if value is None or value.strip() == "":
        raise ValueError(f"Row {row_number}: missing value for {column}")

    return value.strip()