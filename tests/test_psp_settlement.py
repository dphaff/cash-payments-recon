from decimal import Decimal

import pytest

from cash_recon.io.psp_settlement import load_psp_settlement


def test_load_valid_psp_settlement():
    rows = load_psp_settlement("examples/psp_settlement_valid.csv")

    assert len(rows) == 5

    first_row = rows[0]

    assert first_row.psp_transaction_id == "PSP001"
    assert first_row.settlement_batch_id == "BATCH-20260421-001"
    assert first_row.merchant_reference == "ORDER-1001"
    assert first_row.event_type == "PAYMENT"
    assert first_row.gross_amount == Decimal("25.00")
    assert first_row.fee_amount == Decimal("-0.45")
    assert first_row.net_amount == Decimal("24.55")
    assert first_row.currency == "GBP"


def test_invalid_psp_settlement_file_raises_error():
    with pytest.raises(ValueError):
        load_psp_settlement("examples/psp_settlement_invalid.csv")