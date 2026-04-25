from decimal import Decimal

import pytest

from cash_recon.io.bank_receipts import load_bank_receipts


def test_load_valid_bank_receipts():
    receipts = load_bank_receipts("examples/bank_receipts_valid.csv")

    assert len(receipts) == 1

    first_receipt = receipts[0]

    assert first_receipt.bank_transaction_id == "BANK001"
    assert first_receipt.bank_account_id == "MERCHANT-GBP-001"
    assert first_receipt.bank_reference == "PSP PAYOUT BATCH-20260421-001"
    assert first_receipt.amount == Decimal("37.05")
    assert first_receipt.currency == "GBP"


def test_invalid_bank_receipts_file_raises_error():
    with pytest.raises(ValueError):
        load_bank_receipts("examples/bank_receipts_invalid.csv")