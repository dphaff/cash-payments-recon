import csv
from pathlib import Path

from cash_recon.exceptions import ReconException
from cash_recon.recon.internal_psp import InternalPSPReconResult
from cash_recon.recon.psp_bank import PSPBankReconResult


def build_run_output_dir(outdir: str, run_id: str) -> Path:
    output_dir = Path(outdir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    return output_dir


def write_internal_psp_report(
    output_dir: Path,
    results: list[InternalPSPReconResult],
) -> Path:
    output_path = output_dir / "internal_psp_recon.csv"

    fieldnames = [
        "status",
        "merchant_reference",
        "event_type",
        "gross_amount",
        "internal_event_id",
        "psp_transaction_id",
    ]

    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    "status": result.status,
                    "merchant_reference": result.merchant_reference,
                    "event_type": result.event_type,
                    "gross_amount": str(result.gross_amount),
                    "internal_event_id": result.internal_event_id,
                    "psp_transaction_id": result.psp_transaction_id,
                }
            )

    return output_path


def write_psp_bank_report(
    output_dir: Path,
    results: list[PSPBankReconResult],
) -> Path:
    output_path = output_dir / "psp_bank_recon.csv"

    fieldnames = [
        "status",
        "settlement_batch_id",
        "bank_transaction_id",
        "expected_payout_amount",
        "bank_amount",
        "amount_difference",
        "currency",
    ]

    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    "status": result.status,
                    "settlement_batch_id": result.settlement_batch_id,
                    "bank_transaction_id": result.bank_transaction_id,
                    "expected_payout_amount": (
                        str(result.expected_payout_amount)
                        if result.expected_payout_amount is not None
                        else None
                    ),
                    "bank_amount": (
                        str(result.bank_amount)
                        if result.bank_amount is not None
                        else None
                    ),
                    "amount_difference": (
                        str(result.amount_difference)
                        if result.amount_difference is not None
                        else None
                    ),
                    "currency": result.currency,
                }
            )

    return output_path


def write_exceptions_report(
    output_dir: Path,
    exceptions: list[ReconException],
) -> Path:
    output_path = output_dir / "exceptions.csv"

    fieldnames = [
        "exception_type",
        "source_stage",
        "severity",
        "merchant_reference",
        "settlement_batch_id",
        "amount",
        "description",
    ]

    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for exception in exceptions:
            writer.writerow(
                {
                    "exception_type": exception.exception_type,
                    "source_stage": exception.source_stage,
                    "severity": exception.severity,
                    "merchant_reference": exception.merchant_reference,
                    "settlement_batch_id": exception.settlement_batch_id,
                    "amount": (
                        str(exception.amount)
                        if exception.amount is not None
                        else None
                    ),
                    "description": exception.description,
                }
            )

    return output_path