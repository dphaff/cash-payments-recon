import argparse

from cash_recon import __version__


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

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"cash-recon {__version__}")
        return

    parser.print_help()