from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.recon.internal_psp import (
    INTERNAL_MISSING_IN_PSP,
    MATCHED,
    PSP_MISSING_IN_INTERNAL,
    count_psp_fee_rows,
    reconcile_internal_to_psp,
    summarise_internal_psp_results,
)


def test_internal_events_match_psp_settlement_rows():
    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    results = reconcile_internal_to_psp(
        internal_events=internal_events,
        psp_rows=psp_rows,
    )

    summary = summarise_internal_psp_results(results)

    assert summary[MATCHED] == 4
    assert summary[INTERNAL_MISSING_IN_PSP] == 0
    assert summary[PSP_MISSING_IN_INTERNAL] == 0
    assert count_psp_fee_rows(psp_rows) == 1


def test_reconciliation_identifies_internal_event_missing_from_psp():
    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    psp_rows_without_order_1001 = [
        row for row in psp_rows if row.merchant_reference != "ORDER-1001"
    ]

    results = reconcile_internal_to_psp(
        internal_events=internal_events,
        psp_rows=psp_rows_without_order_1001,
    )

    summary = summarise_internal_psp_results(results)

    assert summary[MATCHED] == 3
    assert summary[INTERNAL_MISSING_IN_PSP] == 1
    assert summary[PSP_MISSING_IN_INTERNAL] == 0


def test_reconciliation_identifies_psp_row_missing_from_internal():
    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    internal_events_without_order_1003 = [
        event for event in internal_events if event.merchant_reference != "ORDER-1003"
    ]

    results = reconcile_internal_to_psp(
        internal_events=internal_events_without_order_1003,
        psp_rows=psp_rows,
    )

    summary = summarise_internal_psp_results(results)

    assert summary[MATCHED] == 3
    assert summary[INTERNAL_MISSING_IN_PSP] == 0
    assert summary[PSP_MISSING_IN_INTERNAL] == 1