# BankOps Capability Engine

BankOps Capability Engine discovers workflows in legacy banking user interfaces with an LLM, records successful runs as typed capabilities, and replays those capabilities deterministically without an LLM in the decision loop.

The project uses **LedgerDesk**, a synthetic legacy-style banking application, as its live demonstration surface. No real banking credentials, accounts, or personally identifiable information are used.

## Project status

This repository is under active development. The implementation uses Python, with Jinja2 and Playwright as focused learning areas. See [`STATUS.md`](STATUS.md), [`docs/PLAN.md`](docs/PLAN.md), and [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md).

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
playwright install chromium
```

## Run LedgerDesk

```bash
source .venv/bin/activate
uvicorn ledgerdesk.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`, search for synthetic member `M-10001`, select **Open Member**, and verify the displayed savings balance is `$4,250.75`. Use `M-99999` to exercise the member-not-found business outcome.

## Development checks

```bash
ruff format --check .
ruff check .
mypy
pytest
```

Discovery and deterministic-replay commands will be added when those milestones are implemented.
