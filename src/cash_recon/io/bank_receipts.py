import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


REQUIRED_COLUMNS = [
    "bank_transaction_id",
    "bank_account_id",
    "receipt_date",
    "bank_reference",
    "amount",
    "currency",
]

ALLOWED_CURRENCY = "GBP"


@dataclass
class BankReceipt:
    bank_transaction_id: str
    bank_account_id: str
    receipt_date: date
    bank_reference: str
    amount: Decimal
    currency: str


def load_bank_receipts(file_path: str) -> list[BankReceipt]:
    path = Path(file_path)

    if not path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    with path.open("r", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames != REQUIRED_COLUMNS:
            raise ValueError(
                f"Invalid columns. Expected {REQUIRED_COLUMNS}, got {reader.fieldnames}"
            )

        receipts = []

        for row_number, row in enumerate(reader, start=2):
            receipt = _parse_bank_receipt(row, row_number)
            receipts.append(receipt)

    return receipts


def _parse_bank_receipt(row: dict[str, str], row_number: int) -> BankReceipt:
    bank_transaction_id = _require_value(row, "bank_transaction_id", row_number)
    bank_account_id = _require_value(row, "bank_account_id", row_number)
    receipt_date_raw = _require_value(row, "receipt_date", row_number)
    bank_reference = _require_value(row, "bank_reference", row_number)
    amount_raw = _require_value(row, "amount", row_number)
    currency = _require_value(row, "currency", row_number)

    try:
        receipt_date = date.fromisoformat(receipt_date_raw)
    except ValueError:
        raise ValueError(
            f"Row {row_number}: receipt_date must use YYYY-MM-DD format"
        )

    amount = _parse_decimal(amount_raw, "amount", row_number)

    if amount <= Decimal("0.00"):
        raise ValueError(
            f"Row {row_number}: amount must be positive for a bank receipt"
        )

    if currency != ALLOWED_CURRENCY:
        raise ValueError(
            f"Row {row_number}: currency must be {ALLOWED_CURRENCY}"
        )

    return BankReceipt(
        bank_transaction_id=bank_transaction_id,
        bank_account_id=bank_account_id,
        receipt_date=receipt_date,
        bank_reference=bank_reference,
        amount=amount,
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