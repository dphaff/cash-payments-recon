from dataclasses import dataclass
from decimal import Decimal

from cash_recon.io.bank_receipts import BankReceipt
from cash_recon.recon.psp_batches import PSPBatchTotal


MATCHED = "MATCHED"
EXPECTED_PAYOUT_MISSING_IN_BANK = "EXPECTED_PAYOUT_MISSING_IN_BANK"
BANK_RECEIPT_MISSING_EXPECTED_PAYOUT = "BANK_RECEIPT_MISSING_EXPECTED_PAYOUT"


@dataclass
class PSPBankReconResult:
    status: str
    settlement_batch_id: str | None
    bank_transaction_id: str | None
    expected_payout_amount: Decimal | None
    bank_amount: Decimal | None
    currency: str | None


def reconcile_psp_batches_to_bank(
    batch_totals: list[PSPBatchTotal],
    bank_receipts: list[BankReceipt],
) -> list[PSPBankReconResult]:
    unmatched_bank_receipts = bank_receipts.copy()
    results = []

    for batch in batch_totals:
        matched_bank_receipt = None

        for bank_receipt in unmatched_bank_receipts:
            reference_contains_batch_id = (
                batch.settlement_batch_id in bank_receipt.bank_reference
            )
            amount_matches = batch.expected_payout_amount == bank_receipt.amount
            currency_matches = batch.currency == bank_receipt.currency

            if reference_contains_batch_id and amount_matches and currency_matches:
                matched_bank_receipt = bank_receipt
                break

        if matched_bank_receipt is not None:
            unmatched_bank_receipts.remove(matched_bank_receipt)

            results.append(
                PSPBankReconResult(
                    status=MATCHED,
                    settlement_batch_id=batch.settlement_batch_id,
                    bank_transaction_id=matched_bank_receipt.bank_transaction_id,
                    expected_payout_amount=batch.expected_payout_amount,
                    bank_amount=matched_bank_receipt.amount,
                    currency=batch.currency,
                )
            )
        else:
            results.append(
                PSPBankReconResult(
                    status=EXPECTED_PAYOUT_MISSING_IN_BANK,
                    settlement_batch_id=batch.settlement_batch_id,
                    bank_transaction_id=None,
                    expected_payout_amount=batch.expected_payout_amount,
                    bank_amount=None,
                    currency=batch.currency,
                )
            )

    for bank_receipt in unmatched_bank_receipts:
        results.append(
            PSPBankReconResult(
                status=BANK_RECEIPT_MISSING_EXPECTED_PAYOUT,
                settlement_batch_id=None,
                bank_transaction_id=bank_receipt.bank_transaction_id,
                expected_payout_amount=None,
                bank_amount=bank_receipt.amount,
                currency=bank_receipt.currency,
            )
        )

    return results


def summarise_psp_bank_results(
    results: list[PSPBankReconResult],
) -> dict[str, int]:
    summary = {
        MATCHED: 0,
        EXPECTED_PAYOUT_MISSING_IN_BANK: 0,
        BANK_RECEIPT_MISSING_EXPECTED_PAYOUT: 0,
    }

    for result in results:
        summary[result.status] += 1

    return summary