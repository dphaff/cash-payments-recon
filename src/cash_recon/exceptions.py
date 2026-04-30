from dataclasses import dataclass
from decimal import Decimal

from cash_recon.recon.internal_psp import (
    INTERNAL_MISSING_IN_PSP,
    PSP_MISSING_IN_INTERNAL,
    InternalPSPReconResult,
)
from cash_recon.recon.psp_bank import (
    BANK_RECEIPT_MISSING_EXPECTED_PAYOUT,
    EXPECTED_PAYOUT_MISSING_IN_BANK,
    PSPBankReconResult,
)

from cash_recon.recon.psp_bank import (
    BANK_RECEIPT_MISSING_EXPECTED_PAYOUT,
    EXPECTED_PAYOUT_MISSING_IN_BANK,
    PSPBankReconResult,
)

MISSING_PSP_TRANSACTION = "MISSING_PSP_TRANSACTION"
UNEXPECTED_PSP_TRANSACTION = "UNEXPECTED_PSP_TRANSACTION"
MISSING_BANK_RECEIPT = "MISSING_BANK_RECEIPT"
UNEXPECTED_BANK_RECEIPT = "UNEXPECTED_BANK_RECEIPT"


@dataclass
class ReconException:
    exception_type: str
    source_stage: str
    severity: str
    merchant_reference: str | None
    settlement_batch_id: str | None
    amount: Decimal | None
    description: str


def classify_internal_psp_exceptions(
    results: list[InternalPSPReconResult],
) -> list[ReconException]:
    exceptions = []

    for result in results:
        if result.status == INTERNAL_MISSING_IN_PSP:
            exceptions.append(
                ReconException(
                    exception_type=MISSING_PSP_TRANSACTION,
                    source_stage="INTERNAL_TO_PSP",
                    severity="HIGH",
                    merchant_reference=result.merchant_reference,
                    settlement_batch_id=None,
                    amount=result.gross_amount,
                    description=(
                        "Internal event exists but matching PSP settlement row "
                        "was not found."
                    ),
                )
            )

        if result.status == PSP_MISSING_IN_INTERNAL:
            exceptions.append(
                ReconException(
                    exception_type=UNEXPECTED_PSP_TRANSACTION,
                    source_stage="INTERNAL_TO_PSP",
                    severity="HIGH",
                    merchant_reference=result.merchant_reference,
                    settlement_batch_id=None,
                    amount=result.gross_amount,
                    description=(
                        "PSP settlement row exists but matching internal event "
                        "was not found."
                    ),
                )
            )

    return exceptions


def classify_psp_bank_exceptions(
    results: list[PSPBankReconResult],
) -> list[ReconException]:
    exceptions = []

    for result in results:
        if result.status == EXPECTED_PAYOUT_MISSING_IN_BANK:
            exceptions.append(
                ReconException(
                    exception_type=MISSING_BANK_RECEIPT,
                    source_stage="PSP_TO_BANK",
                    severity="HIGH",
                    merchant_reference=None,
                    settlement_batch_id=result.settlement_batch_id,
                    amount=result.expected_payout_amount,
                    description=(
                        "Expected PSP payout was derived from settlement detail "
                        "but matching bank receipt was not found."
                    ),
                )
            )

        if result.status == BANK_RECEIPT_MISSING_EXPECTED_PAYOUT:
            exceptions.append(
                ReconException(
                    exception_type=UNEXPECTED_BANK_RECEIPT,
                    source_stage="PSP_TO_BANK",
                    severity="MEDIUM",
                    merchant_reference=None,
                    settlement_batch_id=result.settlement_batch_id,
                    amount=result.bank_amount,
                    description=(
                        "Bank receipt exists but matching PSP expected payout "
                        "was not found."
                    ),
                )
            )

    return exceptions


def classify_all_exceptions(
    internal_psp_results: list[InternalPSPReconResult],
    psp_bank_results: list[PSPBankReconResult],
) -> list[ReconException]:
    exceptions = []

    exceptions.extend(
        classify_internal_psp_exceptions(internal_psp_results)
    )

    exceptions.extend(
        classify_psp_bank_exceptions(psp_bank_results)
    )

    return exceptions