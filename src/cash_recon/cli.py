import argparse

from cash_recon import __version__
from cash_recon.db import (
    fetch_open_exceptions_with_ageing,
    initialise_database,
    persist_exceptions,
    record_run,
)
from cash_recon.excel import write_excel_workbook
from cash_recon.exceptions import classify_all_exceptions
from cash_recon.io.bank_receipts import load_bank_receipts
from cash_recon.io.internal_events import load_internal_events
from cash_recon.io.psp_settlement import load_psp_settlement
from cash_recon.mi import build_mi_summary, write_mi_summary_report
from cash_recon.outputs import (
    build_run_output_dir,
    write_exceptions_report,
    write_internal_psp_report,
    write_psp_bank_report,
)
from cash_recon.recon.internal_psp import (
    INTERNAL_MISSING_IN_PSP,
    MATCHED as INTERNAL_PSP_MATCHED,
    PSP_MISSING_IN_INTERNAL,
    count_psp_fee_rows,
    reconcile_internal_to_psp,
    summarise_internal_psp_results,
)
from cash_recon.recon.psp_bank import (
    BANK_RECEIPT_MISSING_EXPECTED_PAYOUT,
    EXPECTED_PAYOUT_MISSING_IN_BANK,
    MATCHED as PSP_BANK_MATCHED,
    reconcile_psp_batches_to_bank,
    summarise_psp_bank_results,
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
    validate_internal_parser.add_argument("--internal", required=True)

    validate_psp_parser = subparsers.add_parser(
        "validate-psp",
        help="Validate a PSP settlement CSV file.",
    )
    validate_psp_parser.add_argument("--psp", required=True)

    validate_bank_parser = subparsers.add_parser(
        "validate-bank",
        help="Validate a bank receipts CSV file.",
    )
    validate_bank_parser.add_argument("--bank", required=True)

    reconcile_internal_psp_parser = subparsers.add_parser(
        "reconcile-internal-psp",
        help="Reconcile internal events to PSP settlement detail.",
    )
    reconcile_internal_psp_parser.add_argument("--internal", required=True)
    reconcile_internal_psp_parser.add_argument("--psp", required=True)

    derive_psp_batches_parser = subparsers.add_parser(
        "derive-psp-batches",
        help="Derive expected PSP settlement batch totals.",
    )
    derive_psp_batches_parser.add_argument("--psp", required=True)

    reconcile_psp_bank_parser = subparsers.add_parser(
        "reconcile-psp-bank",
        help="Reconcile PSP expected batch payouts to bank receipts.",
    )
    reconcile_psp_bank_parser.add_argument("--psp", required=True)
    reconcile_psp_bank_parser.add_argument("--bank", required=True)

    classify_exceptions_parser = subparsers.add_parser(
        "classify-exceptions",
        help="Classify reconciliation exceptions across all stages.",
    )
    classify_exceptions_parser.add_argument("--internal", required=True)
    classify_exceptions_parser.add_argument("--psp", required=True)
    classify_exceptions_parser.add_argument("--bank", required=True)

    init_db_parser = subparsers.add_parser(
        "init-db",
        help="Initialise the SQLite database.",
    )
    init_db_parser.add_argument("--db", required=True)

    record_run_parser = subparsers.add_parser(
        "record-run",
        help="Record a reconciliation run in the database.",
    )
    record_run_parser.add_argument("--db", required=True)
    record_run_parser.add_argument("--run-id", required=True)
    record_run_parser.add_argument(
        "--status",
        required=True,
        choices=["SUCCESS", "FAILED"],
    )

    persist_exceptions_parser = subparsers.add_parser(
        "persist-exceptions",
        help="Classify and persist reconciliation exceptions.",
    )
    persist_exceptions_parser.add_argument("--db", required=True)
    persist_exceptions_parser.add_argument("--run-id", required=True)
    persist_exceptions_parser.add_argument("--internal", required=True)
    persist_exceptions_parser.add_argument("--psp", required=True)
    persist_exceptions_parser.add_argument("--bank", required=True)

    list_open_exceptions_parser = subparsers.add_parser(
        "list-open-exceptions",
        help="List open exceptions with ageing.",
    )
    list_open_exceptions_parser.add_argument("--db", required=True)

    export_reports_parser = subparsers.add_parser(
        "export-reports",
        help="Export reconciliation reports as CSV files.",
    )
    export_reports_parser.add_argument("--run-id", required=True)
    export_reports_parser.add_argument("--internal", required=True)
    export_reports_parser.add_argument("--psp", required=True)
    export_reports_parser.add_argument("--bank", required=True)
    export_reports_parser.add_argument("--outdir", required=True)

    export_mi_summary_parser = subparsers.add_parser(
        "export-mi-summary",
        help="Export daily MI summary as a CSV file.",
    )
    export_mi_summary_parser.add_argument("--run-id", required=True)
    export_mi_summary_parser.add_argument("--internal", required=True)
    export_mi_summary_parser.add_argument("--psp", required=True)
    export_mi_summary_parser.add_argument("--bank", required=True)
    export_mi_summary_parser.add_argument("--outdir", required=True)

    export_excel_parser = subparsers.add_parser(
        "export-excel",
        help="Export reconciliation report as an Excel workbook.",
    )
    export_excel_parser.add_argument("--run-id", required=True)
    export_excel_parser.add_argument("--internal", required=True)
    export_excel_parser.add_argument("--psp", required=True)
    export_excel_parser.add_argument("--bank", required=True)
    export_excel_parser.add_argument("--outdir", required=True)

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
        print(f"Matched: {summary[INTERNAL_PSP_MATCHED]}")
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

    if args.command == "reconcile-psp-bank":
        try:
            psp_rows = load_psp_settlement(args.psp)
            bank_receipts = load_bank_receipts(args.bank)
            batch_totals = derive_psp_batch_totals(psp_rows)
        except ValueError as error:
            print(f"Input file invalid: {error}")
            raise SystemExit(1)

        results = reconcile_psp_batches_to_bank(
            batch_totals=batch_totals,
            bank_receipts=bank_receipts,
        )

        summary = summarise_psp_bank_results(results)

        print("PSP to bank reconciliation complete")
        print(f"Matched: {summary[PSP_BANK_MATCHED]}")
        print(
            "Expected payout missing in bank: "
            f"{summary[EXPECTED_PAYOUT_MISSING_IN_BANK]}"
        )
        print(
            "Bank receipt missing expected payout: "
            f"{summary[BANK_RECEIPT_MISSING_EXPECTED_PAYOUT]}"
        )
        return

    if args.command == "classify-exceptions":
        try:
            internal_events = load_internal_events(args.internal)
            psp_rows = load_psp_settlement(args.psp)
            bank_receipts = load_bank_receipts(args.bank)
            batch_totals = derive_psp_batch_totals(psp_rows)
        except ValueError as error:
            print(f"Input file invalid: {error}")
            raise SystemExit(1)

        internal_psp_results = reconcile_internal_to_psp(
            internal_events=internal_events,
            psp_rows=psp_rows,
        )

        psp_bank_results = reconcile_psp_batches_to_bank(
            batch_totals=batch_totals,
            bank_receipts=bank_receipts,
        )

        exceptions = classify_all_exceptions(
            internal_psp_results=internal_psp_results,
            psp_bank_results=psp_bank_results,
        )

        print("Exception classification complete")
        print(f"Total exceptions: {len(exceptions)}")

        for exception in exceptions:
            print("---")
            print(f"Type: {exception.exception_type}")
            print(f"Stage: {exception.source_stage}")
            print(f"Severity: {exception.severity}")
            print(f"Merchant reference: {exception.merchant_reference}")
            print(f"Settlement batch: {exception.settlement_batch_id}")
            print(f"Amount: {exception.amount}")
            print(f"Description: {exception.description}")

        return

    if args.command == "init-db":
        initialise_database(args.db)
        print(f"Database initialised: {args.db}")
        return

    if args.command == "record-run":
        try:
            record_run(
                db_path=args.db,
                run_id=args.run_id,
                status=args.status,
            )
        except ValueError as error:
            print(f"Run record failed: {error}")
            raise SystemExit(1)

        print(f"Run recorded: {args.run_id}")
        return

    if args.command == "persist-exceptions":
        try:
            internal_events = load_internal_events(args.internal)
            psp_rows = load_psp_settlement(args.psp)
            bank_receipts = load_bank_receipts(args.bank)

            batch_totals = derive_psp_batch_totals(psp_rows)

            internal_psp_results = reconcile_internal_to_psp(
                internal_events=internal_events,
                psp_rows=psp_rows,
            )

            psp_bank_results = reconcile_psp_batches_to_bank(
                batch_totals=batch_totals,
                bank_receipts=bank_receipts,
            )

            exceptions = classify_all_exceptions(
                internal_psp_results=internal_psp_results,
                psp_bank_results=psp_bank_results,
            )

            record_run(
                db_path=args.db,
                run_id=args.run_id,
                status="SUCCESS",
            )

            inserted_count = persist_exceptions(
                db_path=args.db,
                run_id=args.run_id,
                exceptions=exceptions,
            )

        except ValueError as error:
            print(f"Persist exceptions failed: {error}")
            raise SystemExit(1)

        print("Exceptions persisted")
        print(f"Run ID: {args.run_id}")
        print(f"Exceptions inserted: {inserted_count}")
        return

    if args.command == "list-open-exceptions":
        open_exceptions = fetch_open_exceptions_with_ageing(args.db)

        print("Open exceptions")

        if not open_exceptions:
            print("No open exceptions")
            return

        for exception in open_exceptions:
            print(f"Exception ID: {exception['exception_id']}")
            print(f"Run ID: {exception['run_id']}")
            print(f"Type: {exception['exception_type']}")
            print(f"Stage: {exception['source_stage']}")
            print(f"Severity: {exception['severity']}")
            print(f"Amount: {exception['amount']}")
            print(f"Status: {exception['status']}")
            print(f"Age days: {exception['age_days']}")
            print(f"Age bucket: {exception['age_bucket']}")
            print("---")

        return

    if args.command == "export-reports":
        try:
            internal_events = load_internal_events(args.internal)
            psp_rows = load_psp_settlement(args.psp)
            bank_receipts = load_bank_receipts(args.bank)

            batch_totals = derive_psp_batch_totals(psp_rows)

            internal_psp_results = reconcile_internal_to_psp(
                internal_events=internal_events,
                psp_rows=psp_rows,
            )

            psp_bank_results = reconcile_psp_batches_to_bank(
                batch_totals=batch_totals,
                bank_receipts=bank_receipts,
            )

            exceptions = classify_all_exceptions(
                internal_psp_results=internal_psp_results,
                psp_bank_results=psp_bank_results,
            )

            output_dir = build_run_output_dir(
                outdir=args.outdir,
                run_id=args.run_id,
            )

            internal_psp_report = write_internal_psp_report(
                output_dir=output_dir,
                results=internal_psp_results,
            )

            psp_bank_report = write_psp_bank_report(
                output_dir=output_dir,
                results=psp_bank_results,
            )

            exceptions_report = write_exceptions_report(
                output_dir=output_dir,
                exceptions=exceptions,
            )

        except ValueError as error:
            print(f"Report export failed: {error}")
            raise SystemExit(1)

        print("Reports exported")
        print(f"Output folder: {output_dir}")
        print(f"Internal to PSP report: {internal_psp_report}")
        print(f"PSP to bank report: {psp_bank_report}")
        print(f"Exceptions report: {exceptions_report}")
        return

    if args.command == "export-mi-summary":
        try:
            internal_events = load_internal_events(args.internal)
            psp_rows = load_psp_settlement(args.psp)
            bank_receipts = load_bank_receipts(args.bank)

            batch_totals = derive_psp_batch_totals(psp_rows)

            internal_psp_results = reconcile_internal_to_psp(
                internal_events=internal_events,
                psp_rows=psp_rows,
            )

            psp_bank_results = reconcile_psp_batches_to_bank(
                batch_totals=batch_totals,
                bank_receipts=bank_receipts,
            )

            exceptions = classify_all_exceptions(
                internal_psp_results=internal_psp_results,
                psp_bank_results=psp_bank_results,
            )

            mi_summary = build_mi_summary(
                run_id=args.run_id,
                internal_events=internal_events,
                psp_rows=psp_rows,
                bank_receipts=bank_receipts,
                batch_totals=batch_totals,
                internal_psp_results=internal_psp_results,
                psp_bank_results=psp_bank_results,
                exceptions=exceptions,
            )

            output_dir = build_run_output_dir(
                outdir=args.outdir,
                run_id=args.run_id,
            )

            mi_summary_report = write_mi_summary_report(
                output_dir=output_dir,
                summary=mi_summary,
            )

        except ValueError as error:
            print(f"MI summary export failed: {error}")
            raise SystemExit(1)

        print("MI summary exported")
        print(f"Output file: {mi_summary_report}")
        return

    if args.command == "export-excel":
        try:
            internal_events = load_internal_events(args.internal)
            psp_rows = load_psp_settlement(args.psp)
            bank_receipts = load_bank_receipts(args.bank)

            batch_totals = derive_psp_batch_totals(psp_rows)

            internal_psp_results = reconcile_internal_to_psp(
                internal_events=internal_events,
                psp_rows=psp_rows,
            )

            psp_bank_results = reconcile_psp_batches_to_bank(
                batch_totals=batch_totals,
                bank_receipts=bank_receipts,
            )

            exceptions = classify_all_exceptions(
                internal_psp_results=internal_psp_results,
                psp_bank_results=psp_bank_results,
            )

            mi_summary = build_mi_summary(
                run_id=args.run_id,
                internal_events=internal_events,
                psp_rows=psp_rows,
                bank_receipts=bank_receipts,
                batch_totals=batch_totals,
                internal_psp_results=internal_psp_results,
                psp_bank_results=psp_bank_results,
                exceptions=exceptions,
            )

            output_dir = build_run_output_dir(
                outdir=args.outdir,
                run_id=args.run_id,
            )

            excel_workbook = write_excel_workbook(
                output_dir=output_dir,
                mi_summary=mi_summary,
                internal_psp_results=internal_psp_results,
                psp_bank_results=psp_bank_results,
                exceptions=exceptions,
            )

        except ValueError as error:
            print(f"Excel export failed: {error}")
            raise SystemExit(1)

        print("Excel workbook exported")
        print(f"Output file: {excel_workbook}")
        return

    parser.print_help()