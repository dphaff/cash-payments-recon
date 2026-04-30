from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.quality import (
    check_all_duplicates,
    check_internal_duplicates,
    summarise_duplicate_results,
)


def test_valid_demo_files_have_no_duplicates():
    internal_events = load_internal_events("examples/internal_events_valid.csv")
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_valid.csv")

    duplicate_results = check_all_duplicates(
        internal_events=internal_events,
        psp_rows=psp_rows,
        bank_receipts=bank_receipts,
    )

    summary = summarise_duplicate_results(duplicate_results)

    assert summary.internal_duplicate_event_ids == 0
    assert summary.internal_duplicate_match_keys == 0
    assert summary.psp_duplicate_transaction_ids == 0
    assert summary.psp_duplicate_match_keys == 0
    assert summary.bank_duplicate_transaction_ids == 0
    assert summary.bank_duplicate_references == 0


def test_detects_duplicate_internal_event_ids_and_match_keys():
    internal_events = load_internal_events(
        "examples/demo_duplicate_internal_events.csv"
    )

    duplicate_results = check_internal_duplicates(internal_events)
    summary = summarise_duplicate_results(duplicate_results)

    duplicate_types = [result.duplicate_type for result in duplicate_results]

    assert summary.internal_duplicate_event_ids == 1
    assert summary.internal_duplicate_match_keys == 1
    assert "INTERNAL_DUPLICATE_EVENT_ID" in duplicate_types
    assert "INTERNAL_DUPLICATE_MATCH_KEY" in duplicate_types