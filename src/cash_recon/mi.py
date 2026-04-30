import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from cash_recon.exceptions import ReconException
from cash_recon.io.bank_receipts import BankReceipt
from cash_recon.io.internal_events import InternalEvent
from cash_recon.io.psp_settlement import PSPSettlementRow
from cash_recon.recon.internal_psp import (
    INTERNAL_MISSING_IN_PSP,
    MATCHED as INTERNAL_PSP_MATCHED,
    PSP_MISSING_IN_INTERNAL,
    InternalPSPReconResult,
)
from cash_recon.recon.psp_bank import (
    BANK_RECEIPT_MISSING_EXPECTED_PAYOUT,
    EXPECTED_PAYOUT_MISSING_IN_BANK,
    MATCHED as PSP_BANK_MATCHED,
    MATCHED_WITH_TOLERANCE as PSP_BANK_MATCHED_WITH_TOLERANCE,
    PSPBankReconResult,
)
from cash_recon.recon.psp_batches import PSPBatchTotal


@dataclass
class MISummary:
    run_id: str
    internal_event_count: int
    psp_row_count: int
    bank_receipt_count: int
    psp_batch_count: int
    internal_psp_matched_count: int
    internal_missing_in_psp_count: int
    psp_missing_in_internal_count: int
    psp_bank_matched_count: int
    psp_bank_matched_with_tolerance_count: int
    expected_payout_missing_in_bank_count: int
    bank_receipt_missing_expected_payout_count: int
    total_exception_count: int
    high_severity_exception_count: int
    medium_severity_exception_count: int
    total_expected_payout_amount: Decimal
    total_bank_receipt_amount: Decimal


def build_mi_summary(
    run_id: str,
    internal_events: list[InternalEvent],
    psp_rows: list[PSPSettlementRow],
    bank_receipts: list[BankReceipt],
    batch_totals: list[PSPBatchTotal],
    internal_psp_results: list[InternalPSPReconResult],
    psp_bank_results: list[PSPBankReconResult],
    exceptions: list[ReconException],
) -> MISummary:
    return MISummary(
        run_id=run_id,
        internal_event_count=len(internal_events),
        psp_row_count=len(psp_rows),
        bank_receipt_count=len(bank_receipts),
        psp_batch_count=len(batch_totals),
        psp_bank_matched_with_tolerance_count=_count_psp_bank_status(
            psp_bank_results,
            PSP_BANK_MATCHED_WITH_TOLERANCE,
        ),
        internal_psp_matched_count=_count_internal_psp_status(
            internal_psp_results,
            INTERNAL_PSP_MATCHED,
        ),
        internal_missing_in_psp_count=_count_internal_psp_status(
            internal_psp_results,
            INTERNAL_MISSING_IN_PSP,
        ),
        psp_missing_in_internal_count=_count_internal_psp_status(
            internal_psp_results,
            PSP_MISSING_IN_INTERNAL,
        ),
        psp_bank_matched_count=_count_psp_bank_status(
            psp_bank_results,
            PSP_BANK_MATCHED,
        ),
        expected_payout_missing_in_bank_count=_count_psp_bank_status(
            psp_bank_results,
            EXPECTED_PAYOUT_MISSING_IN_BANK,
        ),
        bank_receipt_missing_expected_payout_count=_count_psp_bank_status(
            psp_bank_results,
            BANK_RECEIPT_MISSING_EXPECTED_PAYOUT,
        ),
        total_exception_count=len(exceptions),
        high_severity_exception_count=_count_exception_severity(
            exceptions,
            "HIGH",
        ),
        medium_severity_exception_count=_count_exception_severity(
            exceptions,
            "MEDIUM",
        ),
        total_expected_payout_amount=sum(
            batch.expected_payout_amount for batch in batch_totals
        ),
        total_bank_receipt_amount=sum(
            receipt.amount for receipt in bank_receipts
        ),
    )


def write_mi_summary_report(
    output_dir: Path,
    summary: MISummary,
) -> Path:
    output_path = output_dir / "mi_summary.csv"

    fieldnames = [
        "run_id",
        "internal_event_count",
        "psp_row_count",
        "bank_receipt_count",
        "psp_batch_count",
        "internal_psp_matched_count",
        "internal_missing_in_psp_count",
        "psp_missing_in_internal_count",
        "psp_bank_matched_count",
        "psp_bank_matched_with_tolerance_count",
        "expected_payout_missing_in_bank_count",
        "bank_receipt_missing_expected_payout_count",
        "total_exception_count",
        "high_severity_exception_count",
        "medium_severity_exception_count",
        "total_expected_payout_amount",
        "total_bank_receipt_amount",
    ]

    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "run_id": summary.run_id,
                "internal_event_count": summary.internal_event_count,
                "psp_row_count": summary.psp_row_count,
                "bank_receipt_count": summary.bank_receipt_count,
                "psp_batch_count": summary.psp_batch_count,
                "internal_psp_matched_count": summary.internal_psp_matched_count,
                "internal_missing_in_psp_count": summary.internal_missing_in_psp_count,
                "psp_missing_in_internal_count": summary.psp_missing_in_internal_count,
                "psp_bank_matched_count": summary.psp_bank_matched_count,
                "psp_bank_matched_with_tolerance_count": (
                    summary.psp_bank_matched_with_tolerance_count
                ),
                "expected_payout_missing_in_bank_count": (
                    summary.expected_payout_missing_in_bank_count
                ),
                "bank_receipt_missing_expected_payout_count": (
                    summary.bank_receipt_missing_expected_payout_count
                ),
                "total_exception_count": summary.total_exception_count,
                "high_severity_exception_count": (
                    summary.high_severity_exception_count
                ),
                "medium_severity_exception_count": (
                    summary.medium_severity_exception_count
                ),
                "total_expected_payout_amount": str(
                    summary.total_expected_payout_amount
                ),
                "total_bank_receipt_amount": str(
                    summary.total_bank_receipt_amount
                ),
            }
        )

    return output_path


def _count_internal_psp_status(
    results: list[InternalPSPReconResult],
    status: str,
) -> int:
    count = 0

    for result in results:
        if result.status == status:
            count += 1

    return count


def _count_psp_bank_status(
    results: list[PSPBankReconResult],
    status: str,
) -> int:
    count = 0

    for result in results:
        if result.status == status:
            count += 1

    return count


def _count_exception_severity(
    exceptions: list[ReconException],
    severity: str,
) -> int:
    count = 0

    for exception in exceptions:
        if exception.severity == severity:
            count += 1

    return count