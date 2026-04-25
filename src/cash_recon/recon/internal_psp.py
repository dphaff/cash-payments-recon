from dataclasses import dataclass
from decimal import Decimal

from cash_recon.io.internal_events import InternalEvent
from cash_recon.io.psp_settlement import PSPSettlementRow


MATCHED = "MATCHED"
INTERNAL_MISSING_IN_PSP = "INTERNAL_MISSING_IN_PSP"
PSP_MISSING_IN_INTERNAL = "PSP_MISSING_IN_INTERNAL"


@dataclass
class InternalPSPReconResult:
    status: str
    merchant_reference: str
    event_type: str
    gross_amount: Decimal
    internal_event_id: str | None
    psp_transaction_id: str | None


def reconcile_internal_to_psp(
    internal_events: list[InternalEvent],
    psp_rows: list[PSPSettlementRow],
) -> list[InternalPSPReconResult]:
    psp_rows_by_key: dict[tuple[str, str, Decimal], list[PSPSettlementRow]] = {}

    for psp_row in psp_rows:
        if psp_row.event_type == "FEE":
            continue

        key = _build_key(
            merchant_reference=psp_row.merchant_reference,
            event_type=psp_row.event_type,
            gross_amount=psp_row.gross_amount,
        )

        if key not in psp_rows_by_key:
            psp_rows_by_key[key] = []

        psp_rows_by_key[key].append(psp_row)

    results = []

    for internal_event in internal_events:
        key = _build_key(
            merchant_reference=internal_event.merchant_reference,
            event_type=internal_event.event_type,
            gross_amount=internal_event.gross_amount,
        )

        matching_psp_rows = psp_rows_by_key.get(key, [])

        if matching_psp_rows:
            matched_psp_row = matching_psp_rows.pop(0)

            results.append(
                InternalPSPReconResult(
                    status=MATCHED,
                    merchant_reference=internal_event.merchant_reference,
                    event_type=internal_event.event_type,
                    gross_amount=internal_event.gross_amount,
                    internal_event_id=internal_event.event_id,
                    psp_transaction_id=matched_psp_row.psp_transaction_id,
                )
            )
        else:
            results.append(
                InternalPSPReconResult(
                    status=INTERNAL_MISSING_IN_PSP,
                    merchant_reference=internal_event.merchant_reference,
                    event_type=internal_event.event_type,
                    gross_amount=internal_event.gross_amount,
                    internal_event_id=internal_event.event_id,
                    psp_transaction_id=None,
                )
            )

    for remaining_psp_rows in psp_rows_by_key.values():
        for psp_row in remaining_psp_rows:
            results.append(
                InternalPSPReconResult(
                    status=PSP_MISSING_IN_INTERNAL,
                    merchant_reference=psp_row.merchant_reference,
                    event_type=psp_row.event_type,
                    gross_amount=psp_row.gross_amount,
                    internal_event_id=None,
                    psp_transaction_id=psp_row.psp_transaction_id,
                )
            )

    return results


def summarise_internal_psp_results(
    results: list[InternalPSPReconResult],
) -> dict[str, int]:
    summary = {
        MATCHED: 0,
        INTERNAL_MISSING_IN_PSP: 0,
        PSP_MISSING_IN_INTERNAL: 0,
    }

    for result in results:
        summary[result.status] += 1

    return summary


def count_psp_fee_rows(psp_rows: list[PSPSettlementRow]) -> int:
    fee_count = 0

    for psp_row in psp_rows:
        if psp_row.event_type == "FEE":
            fee_count += 1

    return fee_count


def _build_key(
    merchant_reference: str,
    event_type: str,
    gross_amount: Decimal,
) -> tuple[str, str, Decimal]:
    return merchant_reference, event_type, gross_amount