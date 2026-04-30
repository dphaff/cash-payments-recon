from dataclasses import dataclass
from decimal import Decimal

from cash_recon.io.bank_receipts import BankReceipt
from cash_recon.recon.psp_batches import PSPBatchTotal


MATCHED = "MATCHED"
MATCHED_WITH_TOLERANCE = "MATCHED_WITH_TOLERANCE"
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
    amount_difference: Decimal | None = None


def reconcile_psp_batches_to_bank(
    batch_totals: list[PSPBatchTotal],
    bank_receipts: list[BankReceipt],
    amount_tolerance: Decimal = Decimal("0.00"),
) -> list[PSPBankReconResult]:
    unmatched_bank_receipts = bank_receipts.copy()
    results = []

    for batch in batch_totals:
        exact_match = None
        tolerance_match = None
        tolerance_difference = None

        for bank_receipt in unmatched_bank_receipts:
            reference_contains_batch_id = (
                batch.settlement_batch_id in bank_receipt.bank_reference
            )
            currency_matches = batch.currency == bank_receipt.currency

            if not reference_contains_batch_id or not currency_matches:
                continue

            amount_difference = abs(batch.expected_payout_amount - bank_receipt.amount)

            if amount_difference == Decimal("0.00"):
                exact_match = bank_receipt
                break

            if (
                amount_tolerance > Decimal("0.00")
                and amount_difference <= amount_tolerance
                and tolerance_match is None
            ):
                tolerance_match = bank_receipt
                tolerance_difference = amount_difference

        if exact_match is not None:
            unmatched_bank_receipts.remove(exact_match)

            results.append(
                PSPBankReconResult(
                    status=MATCHED,
                    settlement_batch_id=batch.settlement_batch_id,
                    bank_transaction_id=exact_match.bank_transaction_id,
                    expected_payout_amount=batch.expected_payout_amount,
                    bank_amount=exact_match.amount,
                    currency=batch.currency,
                    amount_difference=Decimal("0.00"),
                )
            )

        elif tolerance_match is not None:
            unmatched_bank_receipts.remove(tolerance_match)

            results.append(
                PSPBankReconResult(
                    status=MATCHED_WITH_TOLERANCE,
                    settlement_batch_id=batch.settlement_batch_id,
                    bank_transaction_id=tolerance_match.bank_transaction_id,
                    expected_payout_amount=batch.expected_payout_amount,
                    bank_amount=tolerance_match.amount,
                    currency=batch.currency,
                    amount_difference=tolerance_difference,
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
                    amount_difference=None,
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
                amount_difference=None,
            )
        )

    return results


def summarise_psp_bank_results(
    results: list[PSPBankReconResult],
) -> dict[str, int]:
    summary = {
        MATCHED: 0,
        MATCHED_WITH_TOLERANCE: 0,
        EXPECTED_PAYOUT_MISSING_IN_BANK: 0,
        BANK_RECEIPT_MISSING_EXPECTED_PAYOUT: 0,
    }

    for result in results:
        summary[result.status] += 1

    return summary