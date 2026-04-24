# Cash / Payments Reconciliation and Exceptions System

## Project Summary

This project simulates a daily cash and payments reconciliation process for a UK merchant receiving GBP card payments via one PSP.

The v1 system will reconcile:

1. Internal payment/refund events to PSP settlement detail
2. PSP-derived expected settlement batches to bank receipts

It will also classify exceptions, persist unresolved exceptions in SQLite, and produce analyst-friendly outputs.

## Tech Stack

- Python
- SQLite
- CSV inputs and outputs
- Excel-friendly reporting
- pytest for tests

## Current Status

Ticket 1 complete:

- Project skeleton
- Python package layout
- Minimal CLI entrypoint
- Basic test setup

## Run the CLI

```bash
cash-recon --version
```