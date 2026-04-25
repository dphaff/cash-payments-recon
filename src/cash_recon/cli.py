import argparse

from cash_recon import __version__
from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.recon.internal_psp import (
    INTERNAL_MISSING_IN_PSP,
    MATCHED,
    PSP_MISSING_IN_INTERNAL,
    count_psp_fee_rows,
    reconcile_internal_to_psp,
    summarise_internal_psp_results,
)
from cash_recon.recon.psp_batches import derive_psp_batch_totals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cash-recon",
        description="Daily cash and payments reconciliation pipeline.",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the application version and exit.",
    )

    subparsers = parser.add_subparsers(dest="command")

    validate_internal_parser = subparsers.add_parser(
        "validate-internal",
        help="Validate an internal events CSV file.",
    )

    validate_internal_parser.add_argument(
        "--internal",
        required=True,
        help="Path to the internal events CSV file.",
    )

    validate_psp_parser = subparsers.add_parser(
        "validate-psp",
        help="Validate a PSP settlement CSV file.",
    )

    validate_psp_parser.add_argument(
        "--psp",
        required=True,
        help="Path to the PSP settlement CSV file.",
    )

    validate_bank_parser = subparsers.add_parser(
        "validate-bank",
        help="Validate a bank receipts CSV file.",
    )

    validate_bank_parser.add_argument(
        "--bank",
        required=True,
        help="Path to the bank receipts CSV file.",
    )

    reconcile_internal_psp_parser = subparsers.add_parser(
        "reconcile-internal-psp",
        help="Reconcile internal events to PSP settlement detail.",
    )

    reconcile_internal_psp_parser.add_argument(
        "--internal",
        required=True,
        help="Path to the internal events CSV file.",
    )

    reconcile_internal_psp_parser.add_argument(
        "--psp",
        required=True,
        help="Path to the PSP settlement CSV file.",
    )

    derive_psp_batches_parser = subparsers.add_parser(
        "derive-psp-batches",
        help="Derive expected PSP settlement batch totals.",
    )

    derive_psp_batches_parser.add_argument(
        "--psp",
        required=True,
        help="Path to the PSP settlement CSV file.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"cash-recon {__version__}")
        return

    if args.command == "validate-internal":
        try:
            events = load_internal_events(args.internal)
        except ValueError as error:
            print(f"Internal file invalid: {error}")
            raise SystemExit(1)

        print(f"Internal file valid: {len(events)} rows")
        return

    if args.command == "validate-psp":
        try:
            rows = load_psp_settlement(args.psp)
        except ValueError as error:
            print(f"PSP file invalid: {error}")
            raise SystemExit(1)

        print(f"PSP file valid: {len(rows)} rows")
        return

    if args.command == "validate-bank":
        try:
            receipts = load_bank_receipts(args.bank)
        except ValueError as error:
            print(f"Bank file invalid: {error}")
            raise SystemExit(1)

        print(f"Bank file valid: {len(receipts)} rows")
        return

    if args.command == "reconcile-internal-psp":
        try:
            internal_events = load_internal_events(args.internal)
            psp_rows = load_psp_settlement(args.psp)
        except ValueError as error:
            print(f"Input file invalid: {error}")
            raise SystemExit(1)

        results = reconcile_internal_to_psp(
            internal_events=internal_events,
            psp_rows=psp_rows,
        )

        summary = summarise_internal_psp_results(results)
        psp_fee_rows_ignored = count_psp_fee_rows(psp_rows)

        print("Internal to PSP reconciliation complete")
        print(f"Matched: {summary[MATCHED]}")
        print(f"Internal missing in PSP: {summary[INTERNAL_MISSING_IN_PSP]}")
        print(f"PSP missing in internal: {summary[PSP_MISSING_IN_INTERNAL]}")
        print(f"PSP fee rows ignored: {psp_fee_rows_ignored}")
        return

    if args.command == "derive-psp-batches":
        try:
            psp_rows = load_psp_settlement(args.psp)
            batch_totals = derive_psp_batch_totals(psp_rows)
        except ValueError as error:
            print(f"PSP batch derivation failed: {error}")
            raise SystemExit(1)

        print("PSP batch totals derived")

        for batch in batch_totals:
            print(f"Batch: {batch.settlement_batch_id}")
            print(f"Settlement date: {batch.settlement_date}")
            print(f"Currency: {batch.currency}")
            print(f"Transaction rows: {batch.transaction_count}")
            print(f"Expected payout amount: {batch.expected_payout_amount}")

        return

    parser.print_help()