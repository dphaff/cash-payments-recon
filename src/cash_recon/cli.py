import argparse

from cash_recon import __version__
from cash_recon.io.internal_events import load_internal_events


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

    parser.print_help()