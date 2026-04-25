from decimal import Decimal

from cash_recon.exceptions import (
    MISSING_BANK_RECEIPT,
    MISSING_PSP_TRANSACTION,
    UNEXPECTED_BANK_RECEIPT,
    UNEXPECTED_PSP_TRANSACTION,
    classify_all_exceptions,
)
from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.recon.internal_psp import reconcile_internal_to_psp
from cash_recon.recon.psp_bank import reconcile_psp_batches_to_bank
from cash_recon.recon.psp_batches import derive_psp_batch_totals


def test_no_exceptions_when_all_reconciliations_match():
    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_valid.csv")
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

    assert exceptions == []


def test_classifies_missing_psp_transaction():
    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    psp_rows_without_order_1001 = [
        row for row in psp_rows if row.merchant_reference != "ORDER-1001"
    ]

    internal_psp_results = reconcile_internal_to_psp(
        internal_events=internal_events,
        psp_rows=psp_rows_without_order_1001,
    )

    exceptions = classify_all_exceptions(
        internal_psp_results=internal_psp_results,
        psp_bank_results=[],
    )

    assert len(exceptions) == 1

    exception = exceptions[0]

    assert exception.exception_type == MISSING_PSP_TRANSACTION
    assert exception.source_stage == "INTERNAL_TO_PSP"
    assert exception.severity == "HIGH"
    assert exception.merchant_reference == "ORDER-1001"
    assert exception.amount == Decimal("25.00")


def test_classifies_unexpected_psp_transaction():
    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    internal_events_without_order_1003 = [
        event for event in internal_events if event.merchant_reference != "ORDER-1003"
    ]

    internal_psp_results = reconcile_internal_to_psp(
        internal_events=internal_events_without_order_1003,
        psp_rows=psp_rows,
    )

    exceptions = classify_all_exceptions(
        internal_psp_results=internal_psp_results,
        psp_bank_results=[],
    )

    assert len(exceptions) == 1

    exception = exceptions[0]

    assert exception.exception_type == UNEXPECTED_PSP_TRANSACTION
    assert exception.source_stage == "INTERNAL_TO_PSP"
    assert exception.severity == "HIGH"
    assert exception.merchant_reference == "ORDER-1003"
    assert exception.amount == Decimal("15.50")


def test_classifies_missing_bank_receipt_and_unexpected_bank_receipt():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_valid.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    bank_receipts[0].amount = Decimal("99.99")

    psp_bank_results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
    )

    exceptions = classify_all_exceptions(
        internal_psp_results=[],
        psp_bank_results=psp_bank_results,
    )

    exception_types = [exception.exception_type for exception in exceptions]

    assert len(exceptions) == 2
    assert MISSING_BANK_RECEIPT in exception_types
    assert UNEXPECTED_BANK_RECEIPT in exception_types