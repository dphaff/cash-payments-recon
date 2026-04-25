from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from cash_recon.io.psp_settlement import PSPSettlementRow


@dataclass
class PSPBatchTotal:
    settlement_batch_id: str
    settlement_date: date
    currency: str
    transaction_count: int
    expected_payout_amount: Decimal


def derive_psp_batch_totals(
    psp_rows: list[PSPSettlementRow],
) -> list[PSPBatchTotal]:
    batches: dict[str, PSPBatchTotal] = {}

    for row in psp_rows:
        if row.settlement_batch_id not in batches:
            batches[row.settlement_batch_id] = PSPBatchTotal(
                settlement_batch_id=row.settlement_batch_id,
                settlement_date=row.settlement_date,
                currency=row.currency,
                transaction_count=0,
                expected_payout_amount=Decimal("0.00"),
            )

        batch = batches[row.settlement_batch_id]

        if row.settlement_date != batch.settlement_date:
            raise ValueError(
                f"Batch {row.settlement_batch_id}: inconsistent settlement_date"
            )

        if row.currency != batch.currency:
            raise ValueError(
                f"Batch {row.settlement_batch_id}: inconsistent currency"
            )

        batch.transaction_count += 1
        batch.expected_payout_amount += row.net_amount

    return list(batches.values())