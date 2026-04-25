import csv
from decimal import Decimal

from cash_recon.exceptions import classify_all_exceptions
from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.mi import build_mi_summary, write_mi_summary_report
from cash_recon.outputs import build_run_output_dir
from cash_recon.recon.internal_psp import reconcile_internal_to_psp
from cash_recon.recon.psp_bank import reconcile_psp_batches_to_bank
from cash_recon.recon.psp_batches import derive_psp_batch_totals


def test_build_mi_summary_for_mismatch_case():
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

    summary = build_mi_summary(
        run_id="RUN-TEST",
        internal_events=internal_events,
        psp_rows=psp_rows,
        bank_receipts=bank_receipts,
        batch_totals=batch_totals,
        internal_psp_results=internal_psp_results,
        psp_bank_results=psp_bank_results,
        exceptions=exceptions,
    )

    assert summary.run_id == "RUN-TEST"
    assert summary.internal_event_count == 4
    assert summary.psp_row_count == 5
    assert summary.bank_receipt_count == 1
    assert summary.psp_batch_count == 1
    assert summary.internal_psp_matched_count == 4
    assert summary.internal_missing_in_psp_count == 0
    assert summary.psp_missing_in_internal_count == 0
    assert summary.psp_bank_matched_count == 0
    assert summary.expected_payout_missing_in_bank_count == 1
    assert summary.bank_receipt_missing_expected_payout_count == 1
    assert summary.total_exception_count == 2
    assert summary.high_severity_exception_count == 1
    assert summary.medium_severity_exception_count == 1
    assert summary.total_expected_payout_amount == Decimal("37.05")
    assert summary.total_bank_receipt_amount == Decimal("99.99")


def test_write_mi_summary_report(tmp_path):
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

    summary = build_mi_summary(
        run_id="RUN-TEST",
        internal_events=internal_events,
        psp_rows=psp_rows,
        bank_receipts=bank_receipts,
        batch_totals=batch_totals,
        internal_psp_results=internal_psp_results,
        psp_bank_results=psp_bank_results,
        exceptions=exceptions,
    )

    output_dir = build_run_output_dir(
        outdir=str(tmp_path),
        run_id="RUN-TEST",
    )

    output_path = write_mi_summary_report(
        output_dir=output_dir,
        summary=summary,
    )

    assert output_path.exists()

    with output_path.open("r", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["run_id"] == "RUN-TEST"
    assert rows[0]["total_exception_count"] == "2"
    assert rows[0]["total_expected_payout_amount"] == "37.05"
    assert rows[0]["total_bank_receipt_amount"] == "99.99"