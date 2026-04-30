from decimal import Decimal

from cash_recon.exceptions import (
    MISSING_BANK_RECEIPT,
    UNEXPECTED_BANK_RECEIPT,
    classify_all_exceptions,
)
from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.mi import build_mi_summary
from cash_recon.recon.internal_psp import (
    INTERNAL_MISSING_IN_PSP,
    MATCHED as INTERNAL_PSP_MATCHED,
    PSP_MISSING_IN_INTERNAL,
    reconcile_internal_to_psp,
    summarise_internal_psp_results,
)
from cash_recon.recon.psp_bank import (
    BANK_RECEIPT_MISSING_EXPECTED_PAYOUT,
    EXPECTED_PAYOUT_MISSING_IN_BANK,
    MATCHED as PSP_BANK_MATCHED,
    reconcile_psp_batches_to_bank,
    summarise_psp_bank_results,
)
from cash_recon.recon.psp_batches import derive_psp_batch_totals


def test_demo2_internal_psp_reconciliation_matches_all_non_fee_rows():
    internal_events = load_internal_events("examples/demo2_internal_events.csv")
    psp_rows = load_psp_settlement("examples/demo2_psp_settlement.csv")

    results = reconcile_internal_to_psp(
        internal_events=internal_events,
        psp_rows=psp_rows,
    )

    summary = summarise_internal_psp_results(results)

    assert summary[INTERNAL_PSP_MATCHED] == 7
    assert summary[INTERNAL_MISSING_IN_PSP] == 0
    assert summary[PSP_MISSING_IN_INTERNAL] == 0


def test_demo2_derives_two_psp_batch_totals():
    psp_rows = load_psp_settlement("examples/demo2_psp_settlement.csv")

    batch_totals = derive_psp_batch_totals(psp_rows)

    totals_by_batch_id = {
        batch.settlement_batch_id: batch.expected_payout_amount
        for batch in batch_totals
    }

    assert len(batch_totals) == 2
    assert totals_by_batch_id["BATCH-20260502-001"] == Decimal("46.99")
    assert totals_by_batch_id["BATCH-20260503-001"] == Decimal("107.97")


def test_demo2_psp_bank_reconciliation_has_one_match_and_one_mismatch():
    psp_rows = load_psp_settlement("examples/demo2_psp_settlement.csv")
    bank_receipts = load_bank_receipts("examples/demo2_bank_receipts.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
    )

    summary = summarise_psp_bank_results(results)

    assert summary[PSP_BANK_MATCHED] == 1
    assert summary[EXPECTED_PAYOUT_MISSING_IN_BANK] == 1
    assert summary[BANK_RECEIPT_MISSING_EXPECTED_PAYOUT] == 1


def test_demo2_classifies_two_bank_exceptions():
    internal_events = load_internal_events("examples/demo2_internal_events.csv")
    psp_rows = load_psp_settlement("examples/demo2_psp_settlement.csv")
    bank_receipts = load_bank_receipts("examples/demo2_bank_receipts.csv")
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

    exception_types = [exception.exception_type for exception in exceptions]

    assert len(exceptions) == 2
    assert MISSING_BANK_RECEIPT in exception_types
    assert UNEXPECTED_BANK_RECEIPT in exception_types


def test_demo2_mi_summary():
    internal_events = load_internal_events("examples/demo2_internal_events.csv")
    psp_rows = load_psp_settlement("examples/demo2_psp_settlement.csv")
    bank_receipts = load_bank_receipts("examples/demo2_bank_receipts.csv")
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
        run_id="DEMO2-RUN-TEST",
        internal_events=internal_events,
        psp_rows=psp_rows,
        bank_receipts=bank_receipts,
        batch_totals=batch_totals,
        internal_psp_results=internal_psp_results,
        psp_bank_results=psp_bank_results,
        exceptions=exceptions,
    )

    assert summary.internal_event_count == 7
    assert summary.psp_row_count == 9
    assert summary.bank_receipt_count == 2
    assert summary.psp_batch_count == 2
    assert summary.internal_psp_matched_count == 7
    assert summary.psp_bank_matched_count == 1
    assert summary.expected_payout_missing_in_bank_count == 1
    assert summary.bank_receipt_missing_expected_payout_count == 1
    assert summary.total_exception_count == 2
    assert summary.total_expected_payout_amount == Decimal("154.96")
    assert summary.total_bank_receipt_amount == Decimal("146.99")