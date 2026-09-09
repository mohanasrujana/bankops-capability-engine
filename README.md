# BankOps Capability Engine

BankOps Capability Engine discovers workflows in legacy banking user interfaces with an LLM, records successful runs as typed capabilities, and replays those capabilities deterministically without an LLM in the decision loop.

The project uses **LedgerDesk**, a synthetic legacy-style banking application, as its live demonstration surface. No real banking credentials, accounts, or personally identifiable information are used.

## Project status

This repository is under active development. The implementation uses Python, with Jinja2 and Playwright as focused learning areas. See [`STATUS.md`](STATUS.md), [`docs/PLAN.md`](docs/PLAN.md), and [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md).

## Development checks

Verified setup and demonstration commands will be added as the Python implementation reaches runnable milestones.
