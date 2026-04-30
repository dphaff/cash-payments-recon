from decimal import Decimal

from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.recon.psp_bank import (
    BANK_RECEIPT_MISSING_EXPECTED_PAYOUT,
    EXPECTED_PAYOUT_MISSING_IN_BANK,
    MATCHED,
    MATCHED_WITH_TOLERANCE,
    reconcile_psp_batches_to_bank,
    summarise_psp_bank_results,
)
from cash_recon.recon.psp_batches import derive_psp_batch_totals


def test_psp_batch_matches_bank_receipt():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_valid.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
    )

    summary = summarise_psp_bank_results(results)

    assert summary[MATCHED] == 1
    assert summary[MATCHED_WITH_TOLERANCE] == 0
    assert summary[EXPECTED_PAYOUT_MISSING_IN_BANK] == 0
    assert summary[BANK_RECEIPT_MISSING_EXPECTED_PAYOUT] == 0


def test_psp_batch_missing_from_bank_when_reference_does_not_match():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_valid.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    bank_receipts[0].bank_reference = "PSP PAYOUT UNKNOWN-BATCH"

    results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
    )

    summary = summarise_psp_bank_results(results)

    assert summary[MATCHED] == 0
    assert summary[MATCHED_WITH_TOLERANCE] == 0
    assert summary[EXPECTED_PAYOUT_MISSING_IN_BANK] == 1
    assert summary[BANK_RECEIPT_MISSING_EXPECTED_PAYOUT] == 1


def test_psp_batch_missing_from_bank_when_amount_does_not_match_without_tolerance():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_valid.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    bank_receipts[0].amount = Decimal("99.99")

    results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
    )

    summary = summarise_psp_bank_results(results)

    assert summary[MATCHED] == 0
    assert summary[MATCHED_WITH_TOLERANCE] == 0
    assert summary[EXPECTED_PAYOUT_MISSING_IN_BANK] == 1
    assert summary[BANK_RECEIPT_MISSING_EXPECTED_PAYOUT] == 1


def test_psp_batch_matches_with_tolerance_when_amount_difference_is_allowed():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_tolerance.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
        amount_tolerance=Decimal("0.01"),
    )

    summary = summarise_psp_bank_results(results)

    assert summary[MATCHED] == 0
    assert summary[MATCHED_WITH_TOLERANCE] == 1
    assert summary[EXPECTED_PAYOUT_MISSING_IN_BANK] == 0
    assert summary[BANK_RECEIPT_MISSING_EXPECTED_PAYOUT] == 0

    assert results[0].amount_difference == Decimal("0.01")


def test_psp_batch_does_not_match_with_tolerance_when_difference_is_too_large():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")
    bank_receipts = load_bank_receipts("examples/bank_receipts_tolerance.csv")
    batch_totals = derive_psp_batch_totals(psp_rows)

    results = reconcile_psp_batches_to_bank(
        batch_totals=batch_totals,
        bank_receipts=bank_receipts,
        amount_tolerance=Decimal("0.00"),
    )

    summary = summarise_psp_bank_results(results)

    assert summary[MATCHED] == 0
    assert summary[MATCHED_WITH_TOLERANCE] == 0
    assert summary[EXPECTED_PAYOUT_MISSING_IN_BANK] == 1
    assert summary[BANK_RECEIPT_MISSING_EXPECTED_PAYOUT] == 1