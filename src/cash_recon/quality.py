from dataclasses import dataclass
from decimal import Decimal

from cash_recon.io.bank_receipts import BankReceipt
from cash_recon.io.internal_events import InternalEvent
from cash_recon.io.psp_settlement import PSPSettlementRow


@dataclass
class DuplicateCheckResult:
    duplicate_type: str
    duplicate_value: str
    count: int


@dataclass
class DuplicateCheckSummary:
    internal_duplicate_event_ids: int
    internal_duplicate_match_keys: int
    psp_duplicate_transaction_ids: int
    psp_duplicate_match_keys: int
    bank_duplicate_transaction_ids: int
    bank_duplicate_references: int


def check_internal_duplicates(
    internal_events: list[InternalEvent],
) -> list[DuplicateCheckResult]:
    results = []

    event_id_counts: dict[str, int] = {}
    match_key_counts: dict[str, int] = {}

    for event in internal_events:
        event_id_counts[event.event_id] = event_id_counts.get(event.event_id, 0) + 1

        match_key = _format_match_key(
            merchant_reference=event.merchant_reference,
            event_type=event.event_type,
            gross_amount=event.gross_amount,
        )

        match_key_counts[match_key] = match_key_counts.get(match_key, 0) + 1

    results.extend(
        _build_duplicate_results(
            duplicate_type="INTERNAL_DUPLICATE_EVENT_ID",
            counts=event_id_counts,
        )
    )

    results.extend(
        _build_duplicate_results(
            duplicate_type="INTERNAL_DUPLICATE_MATCH_KEY",
            counts=match_key_counts,
        )
    )

    return results


def check_psp_duplicates(
    psp_rows: list[PSPSettlementRow],
) -> list[DuplicateCheckResult]:
    results = []

    transaction_id_counts: dict[str, int] = {}
    match_key_counts: dict[str, int] = {}

    for row in psp_rows:
        transaction_id_counts[row.psp_transaction_id] = (
            transaction_id_counts.get(row.psp_transaction_id, 0) + 1
        )

        if row.event_type == "FEE":
            continue

        match_key = _format_match_key(
            merchant_reference=row.merchant_reference,
            event_type=row.event_type,
            gross_amount=row.gross_amount,
        )

        match_key_counts[match_key] = match_key_counts.get(match_key, 0) + 1

    results.extend(
        _build_duplicate_results(
            duplicate_type="PSP_DUPLICATE_TRANSACTION_ID",
            counts=transaction_id_counts,
        )
    )

    results.extend(
        _build_duplicate_results(
            duplicate_type="PSP_DUPLICATE_MATCH_KEY",
            counts=match_key_counts,
        )
    )

    return results


def check_bank_duplicates(
    bank_receipts: list[BankReceipt],
) -> list[DuplicateCheckResult]:
    results = []

    transaction_id_counts: dict[str, int] = {}
    reference_counts: dict[str, int] = {}

    for receipt in bank_receipts:
        transaction_id_counts[receipt.bank_transaction_id] = (
            transaction_id_counts.get(receipt.bank_transaction_id, 0) + 1
        )

        reference_counts[receipt.bank_reference] = (
            reference_counts.get(receipt.bank_reference, 0) + 1
        )

    results.extend(
        _build_duplicate_results(
            duplicate_type="BANK_DUPLICATE_TRANSACTION_ID",
            counts=transaction_id_counts,
        )
    )

    results.extend(
        _build_duplicate_results(
            duplicate_type="BANK_DUPLICATE_REFERENCE",
            counts=reference_counts,
        )
    )

    return results


def check_all_duplicates(
    internal_events: list[InternalEvent],
    psp_rows: list[PSPSettlementRow],
    bank_receipts: list[BankReceipt],
) -> list[DuplicateCheckResult]:
    results = []

    results.extend(check_internal_duplicates(internal_events))
    results.extend(check_psp_duplicates(psp_rows))
    results.extend(check_bank_duplicates(bank_receipts))

    return results


def summarise_duplicate_results(
    duplicate_results: list[DuplicateCheckResult],
) -> DuplicateCheckSummary:
    return DuplicateCheckSummary(
        internal_duplicate_event_ids=_count_type(
            duplicate_results,
            "INTERNAL_DUPLICATE_EVENT_ID",
        ),
        internal_duplicate_match_keys=_count_type(
            duplicate_results,
            "INTERNAL_DUPLICATE_MATCH_KEY",
        ),
        psp_duplicate_transaction_ids=_count_type(
            duplicate_results,
            "PSP_DUPLICATE_TRANSACTION_ID",
        ),
        psp_duplicate_match_keys=_count_type(
            duplicate_results,
            "PSP_DUPLICATE_MATCH_KEY",
        ),
        bank_duplicate_transaction_ids=_count_type(
            duplicate_results,
            "BANK_DUPLICATE_TRANSACTION_ID",
        ),
        bank_duplicate_references=_count_type(
            duplicate_results,
            "BANK_DUPLICATE_REFERENCE",
        ),
    )


def _build_duplicate_results(
    duplicate_type: str,
    counts: dict[str, int],
) -> list[DuplicateCheckResult]:
    results = []

    for value, count in counts.items():
        if count > 1:
            results.append(
                DuplicateCheckResult(
                    duplicate_type=duplicate_type,
                    duplicate_value=value,
                    count=count,
                )
            )

    return results


def _format_match_key(
    merchant_reference: str,
    event_type: str,
    gross_amount: Decimal,
) -> str:
    return f"{merchant_reference}|{event_type}|{gross_amount}"


def _count_type(
    duplicate_results: list[DuplicateCheckResult],
    duplicate_type: str,
) -> int:
    count = 0

    for result in duplicate_results:
        if result.duplicate_type == duplicate_type:
            count += 1

    return count