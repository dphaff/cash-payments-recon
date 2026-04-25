# Cash / Payments Reconciliation and Exceptions System

## Project Summary

This project simulates a daily cash and payments reconciliation process for a UK merchant receiving GBP card payments through one payment service provider (PSP).

The system validates input files, reconciles internal merchant events to PSP settlement detail, derives expected PSP settlement batch totals, reconciles expected payouts to bank receipts, classifies exceptions, persists open breaks in SQLite, and exports analyst-friendly CSV and Excel reports.

The project is designed as a portfolio piece for operations, reconciliations, payments operations, fintech operations, middle office, MI/reporting, and operational controls roles.

---

## Business Scenario

A UK merchant receives GBP card payments via one PSP.

The PSP settles net funds daily into one GBP bank account.

Operations performs daily reconciliation across:

1. **Internal event ledger**
   - merchant-side payments and refunds

2. **PSP settlement detail**
   - transaction-level PSP settlement records
   - gross amounts
   - PSP fees
   - net settlement amounts
   - settlement batch IDs

3. **Bank receipt extract**
   - bank-side evidence of PSP payout receipt

The operational goal is to confirm:

```text
internal merchant events
        ↓
PSP settlement detail
        ↓
expected PSP payout
        ↓
bank receipt
```

---

## Scope

### In Scope for v1

- One merchant
- One PSP
- One GBP bank account
- One currency: GBP
- Daily batch process
- Internal event ledger
- PSP transaction-level settlement detail
- Bank receipt extract
- Payments, refunds, and PSP fees
- Two-stage reconciliation
- Exception classification
- SQLite run history
- SQLite exception queue
- Open exception ageing
- CSV outputs
- Daily MI summary
- Excel workbook export

### Out of Scope for v1

- Multi-currency
- Multiple PSPs
- Chargebacks
- Manual adjustments
- Partial captures
- Reserve movements
- Rolling holds
- FX
- Real-time processing
- UI / web app
- Manual case editing workflow

---

## Reconciliation Design

### Stage 1 — Internal Events to PSP Settlement Detail

The first control checks whether merchant-side events appear correctly in the PSP settlement file.

Match key:

```text
merchant_reference + event_type + gross_amount
```

PSP fee rows are ignored in this stage because fees do not originate from the internal merchant event ledger.

Possible outcomes:

| Status | Meaning |
|---|---|
| `MATCHED` | Internal event has matching PSP row |
| `INTERNAL_MISSING_IN_PSP` | Internal event not found in PSP detail |
| `PSP_MISSING_IN_INTERNAL` | PSP row not found in internal ledger |

### Stage 2 — PSP Expected Payout to Bank Receipt

The second control checks whether the expected PSP batch payout arrived in the bank account.

The system derives expected payout totals from PSP transaction-level detail:

```text
expected payout = sum(net_amount) by settlement_batch_id
```

It then matches each derived PSP batch total to a bank receipt using:

```text
settlement_batch_id contained in bank_reference
+
amount match
+
currency match
```

Possible outcomes:

| Status | Meaning |
|---|---|
| `MATCHED` | Expected PSP payout matched to bank receipt |
| `EXPECTED_PAYOUT_MISSING_IN_BANK` | PSP expected payout not found in bank |
| `BANK_RECEIPT_MISSING_EXPECTED_PAYOUT` | Bank receipt not explained by PSP expected payout |

---

## Exception Classification

Raw reconciliation breaks are converted into analyst-friendly exception categories.

| Raw status | Exception type |
|---|---|
| `INTERNAL_MISSING_IN_PSP` | `MISSING_PSP_TRANSACTION` |
| `PSP_MISSING_IN_INTERNAL` | `UNEXPECTED_PSP_TRANSACTION` |
| `EXPECTED_PAYOUT_MISSING_IN_BANK` | `MISSING_BANK_RECEIPT` |
| `BANK_RECEIPT_MISSING_EXPECTED_PAYOUT` | `UNEXPECTED_BANK_RECEIPT` |

Open exceptions can be listed with ageing buckets:

```text
0-1 days
2-3 days
4-7 days
8+ days
```

---

## Tech Stack

- Python
- SQLite
- SQL
- CSV input/output
- Excel workbook export
- pytest
- openpyxl

---

## Project Structure

```text
cash-payments-recon/
├── examples/
│   ├── internal_events_valid.csv
│   ├── internal_events_invalid.csv
│   ├── psp_settlement_valid.csv
│   ├── psp_settlement_invalid.csv
│   ├── bank_receipts_valid.csv
│   ├── bank_receipts_invalid.csv
│   └── bank_receipts_mismatch.csv
├── src/
│   └── cash_recon/
│       ├── cli.py
│       ├── db.py
│       ├── exceptions.py
│       ├── excel.py
│       ├── mi.py
│       ├── outputs.py
│       ├── io/
│       │   ├── internal_events.py
│       │   ├── psp_settlement.py
│       │   └── bank_receipts.py
│       └── recon/
│           ├── internal_psp.py
│           ├── psp_batches.py
│           └── psp_bank.py
├── tests/
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

---

## Run Tests

```bash
pytest
```

Expected result:

```text
34 passed
```

The exact number may change as more tests are added.

---

## CLI Commands

### Show Version

```bash
cash-recon --version
```

### Validate Internal Events

```bash
cash-recon validate-internal --internal examples/internal_events_valid.csv
```

### Validate PSP Settlement Detail

```bash
cash-recon validate-psp --psp examples/psp_settlement_valid.csv
```

### Validate Bank Receipts

```bash
cash-recon validate-bank --bank examples/bank_receipts_valid.csv
```

### Reconcile Internal Events to PSP

```bash
cash-recon reconcile-internal-psp \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv
```

### Derive PSP Batch Totals

```bash
cash-recon derive-psp-batches --psp examples/psp_settlement_valid.csv
```

### Reconcile PSP Expected Payout to Bank

```bash
cash-recon reconcile-psp-bank \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_valid.csv
```

### Classify Exceptions

```bash
cash-recon classify-exceptions \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv
```

### Initialise SQLite Database

```bash
cash-recon init-db --db data/recon.sqlite3
```

### Persist Exceptions

```bash
cash-recon persist-exceptions \
  --db data/recon.sqlite3 \
  --run-id RUN-001 \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv
```

### List Open Exceptions with Ageing

```bash
cash-recon list-open-exceptions --db data/recon.sqlite3
```

### Export Detailed CSV Reports

```bash
cash-recon export-reports \
  --run-id RUN-002 \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv \
  --outdir out
```

### Export Daily MI Summary CSV

```bash
cash-recon export-mi-summary \
  --run-id RUN-003 \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv \
  --outdir out
```

### Export Excel Workbook

```bash
cash-recon export-excel \
  --run-id RUN-004 \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv \
  --outdir out
```

This creates:

```text
out/RUN-004/reconciliation_report.xlsx
```

Workbook sheets:

```text
MI Summary
Internal to PSP
PSP to Bank
Exceptions
```

---

## Full Demo Flow

Run these commands from the project root.

```bash
cash-recon validate-internal --internal examples/internal_events_valid.csv
cash-recon validate-psp --psp examples/psp_settlement_valid.csv
cash-recon validate-bank --bank examples/bank_receipts_valid.csv
```

Run the two reconciliation stages:

```bash
cash-recon reconcile-internal-psp \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv
```

```bash
cash-recon reconcile-psp-bank \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_valid.csv
```

Run a mismatch case that creates exceptions:

```bash
cash-recon classify-exceptions \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv
```

Persist those exceptions:

```bash
cash-recon persist-exceptions \
  --db data/recon.sqlite3 \
  --run-id DEMO-RUN-001 \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv
```

List open aged exceptions:

```bash
cash-recon list-open-exceptions --db data/recon.sqlite3
```

Export reports:

```bash
cash-recon export-reports \
  --run-id DEMO-RUN-002 \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv \
  --outdir out
```

Export MI summary:

```bash
cash-recon export-mi-summary \
  --run-id DEMO-RUN-003 \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv \
  --outdir out
```

Export Excel workbook:

```bash
cash-recon export-excel \
  --run-id DEMO-RUN-004 \
  --internal examples/internal_events_valid.csv \
  --psp examples/psp_settlement_valid.csv \
  --bank examples/bank_receipts_mismatch.csv \
  --outdir out
```

---

## Example Output Files

CSV reports:

```text
out/<run_id>/internal_psp_recon.csv
out/<run_id>/psp_bank_recon.csv
out/<run_id>/exceptions.csv
out/<run_id>/mi_summary.csv
```

Excel workbook:

```text
out/<run_id>/reconciliation_report.xlsx
```

Local SQLite database:

```text
data/recon.sqlite3
```

Generated files in `out/` and `data/` are ignored by Git.

---

## What This Project Demonstrates

This project demonstrates:

- payment reconciliation workflow understanding
- cash settlement control design
- internal ledger to external provider reconciliation
- PSP net settlement derivation
- bank receipt matching
- exception classification
- persisted exception queue design
- ageing logic for unresolved breaks
- run history and auditability
- analyst-friendly CSV reporting
- Excel workbook output
- Python CLI development
- SQLite persistence
- pytest test coverage

---

## Portfolio Positioning

This project is intended to demonstrate the ability to bridge operations and data.

It is relevant to roles such as:

- Operations Analyst
- Reconciliations Analyst
- Payments Operations Analyst
- Investment Operations Analyst
- Middle Office Analyst
- Trade Support Analyst
- Operations Data Analyst
- MI / Reporting Analyst
- Process and Controls Analyst

The core value shown is:

```text
I can understand an operational finance process, define control points, implement deterministic reconciliation logic, classify exceptions, persist unresolved breaks, and produce outputs usable by analysts and managers.
```

---

## Possible Future Enhancements

Possible v2 improvements:

- second demo dataset with multiple settlement batches
- Power BI dashboard layer
- configurable PSP mapping rules
- exception closure workflow
- duplicate detection
- tolerance-based matching
- multi-currency handling
- chargeback handling
- manual adjustment support
- richer SQL MI views
- HTML or Streamlit dashboard
