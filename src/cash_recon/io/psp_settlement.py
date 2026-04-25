import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


REQUIRED_COLUMNS = [
    "psp_transaction_id",
    "settlement_batch_id",
    "settlement_date",
    "merchant_reference",
    "event_type",
    "gross_amount",
    "fee_amount",
    "net_amount",
    "currency",
]

ALLOWED_EVENT_TYPES = {"PAYMENT", "REFUND", "FEE"}
ALLOWED_CURRENCY = "GBP"


@dataclass
class PSPSettlementRow:
    psp_transaction_id: str
    settlement_batch_id: str
    settlement_date: date
    merchant_reference: str
    event_type: str
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    currency: str


def load_psp_settlement(file_path: str) -> list[PSPSettlementRow]:
    path = Path(file_path)

    if not path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    with path.open("r", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames != REQUIRED_COLUMNS:
            raise ValueError(
                f"Invalid columns. Expected {REQUIRED_COLUMNS}, got {reader.fieldnames}"
            )

        rows = []

        for row_number, row in enumerate(reader, start=2):
            settlement_row = _parse_psp_settlement_row(row, row_number)
            rows.append(settlement_row)

    return rows


def _parse_psp_settlement_row(
    row: dict[str, str],
    row_number: int,
) -> PSPSettlementRow:
    psp_transaction_id = _require_value(row, "psp_transaction_id", row_number)
    settlement_batch_id = _require_value(row, "settlement_batch_id", row_number)
    settlement_date_raw = _require_value(row, "settlement_date", row_number)
    merchant_reference = _require_value(row, "merchant_reference", row_number)
    event_type = _require_value(row, "event_type", row_number)
    gross_amount_raw = _require_value(row, "gross_amount", row_number)
    fee_amount_raw = _require_value(row, "fee_amount", row_number)
    net_amount_raw = _require_value(row, "net_amount", row_number)
    currency = _require_value(row, "currency", row_number)

    try:
        settlement_date = date.fromisoformat(settlement_date_raw)
    except ValueError:
        raise ValueError(
            f"Row {row_number}: settlement_date must use YYYY-MM-DD format"
        )

    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(
            f"Row {row_number}: event_type must be one of {sorted(ALLOWED_EVENT_TYPES)}"
        )

    gross_amount = _parse_decimal(gross_amount_raw, "gross_amount", row_number)
    fee_amount = _parse_decimal(fee_amount_raw, "fee_amount", row_number)
    net_amount = _parse_decimal(net_amount_raw, "net_amount", row_number)

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

    if event_type == "FEE" and gross_amount != Decimal("0.00"):
        raise ValueError(
            f"Row {row_number}: FEE gross_amount must be 0.00"
        )

    expected_net_amount = gross_amount + fee_amount

    if net_amount != expected_net_amount:
        raise ValueError(
            f"Row {row_number}: net_amount must equal gross_amount + fee_amount"
        )

    return PSPSettlementRow(
        psp_transaction_id=psp_transaction_id,
        settlement_batch_id=settlement_batch_id,
        settlement_date=settlement_date,
        merchant_reference=merchant_reference,
        event_type=event_type,
        gross_amount=gross_amount,
        fee_amount=fee_amount,
        net_amount=net_amount,
        currency=currency,
    )


def _parse_decimal(raw_value: str, column: str, row_number: int) -> Decimal:
    try:
        return Decimal(raw_value)
    except InvalidOperation:
        raise ValueError(
            f"Row {row_number}: {column} must be a valid number"
        )


def _require_value(row: dict[str, str], column: str, row_number: int) -> str:
    value = row.get(column)

    if value is None or value.strip() == "":
        raise ValueError(f"Row {row_number}: missing value for {column}")

    return value.strip()