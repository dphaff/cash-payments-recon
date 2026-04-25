import csv

from cash_recon.exceptions import classify_all_exceptions
from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.outputs import (
    build_run_output_dir,
    write_exceptions_report,
    write_internal_psp_report,
    write_psp_bank_report,
)
from cash_recon.recon.internal_psp import reconcile_internal_to_psp
from cash_recon.recon.psp_bank import reconcile_psp_batches_to_bank
from cash_recon.recon.psp_batches import derive_psp_batch_totals


def test_write_internal_psp_report(tmp_path):
    output_dir = build_run_output_dir(
        outdir=str(tmp_path),
        run_id="RUN-TEST",
    )

    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    results = reconcile_internal_to_psp(
        internal_events=internal_events,
        psp_rows=psp_rows,
    )

    output_path = write_internal_psp_report(
        output_dir=output_dir,
        results=results,
    )

    assert output_path.exists()

    with output_path.open("r", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 4
    assert rows[0]["status"] == "MATCHED"
    assert rows[0]["merchant_reference"] == "ORDER-1001"


def test_write_psp_bank_report(tmp_path):
    output_dir = build_run_output_dir(
        outdir=str(tmp_path),
        run_id="RUN-TEST",
    )

    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_valid.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
    )

    output_path = write_psp_bank_report(
        output_dir=output_dir,
        results=results,
    )

    assert output_path.exists()

    with output_path.open("r", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["status"] == "MATCHED"
    assert rows[0]["expected_payout_amount"] == "37.05"


def test_write_exceptions_report_for_mismatch_case(tmp_path):
    output_dir = build_run_output_dir(
        outdir=str(tmp_path),
        run_id="RUN-TEST",
    )

    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_mismatch.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    internal_psp_results = reconcile_internal_to_psp(
        internal_events=internal_events,
        psp_rows=psp_rows,
    )

    psp_bank_results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
    )

    exceptions = classify_all_exceptions(
        internal_psp_results=internal_psp_results,
        psp_bank_results=psp_bank_results,
    )

    output_path = write_exceptions_report(
        output_dir=output_dir,
        exceptions=exceptions,
    )

    assert output_path.exists()

    with output_path.open("r", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    exception_types = [row["exception_type"] for row in rows]

    assert len(rows) == 2
    assert "MISSING_BANK_RECEIPT" in exception_types
    assert "UNEXPECTED_BANK_RECEIPT" in exception_types