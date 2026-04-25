import argparse

from cash_recon import __version__
from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement


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

    parser.print_help()