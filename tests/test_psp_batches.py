from decimal import Decimal

import pytest

from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.recon.psp_batches import derive_psp_batch_totals


def test_derive_psp_batch_totals():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    batch_totals = derive_psp_batch_totals(psp_rows)

    assert len(batch_totals) == 1

    batch = batch_totals[0]

    assert batch.settlement_batch_id == "BATCH-20260421-001"
    assert str(batch.settlement_date) == "2026-04-21"
    assert batch.currency == "GBP"
    assert batch.transaction_count == 5
    assert batch.expected_payout_amount == Decimal("37.05")


def test_derive_psp_batch_totals_rejects_inconsistent_currency():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    psp_rows[0].currency = "EUR"

    with pytest.raises(ValueError):
        derive_psp_batch_totals(psp_rows)


def test_derive_psp_batch_totals_rejects_inconsistent_settlement_date():
    psp_rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    psp_rows[0].settlement_date = psp_rows[0].settlement_date.replace(day=22)

    with pytest.raises(ValueError):
        derive_psp_batch_totals(psp_rows)