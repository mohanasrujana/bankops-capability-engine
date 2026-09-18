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

## Run deterministic replay

Keep LedgerDesk running in the first terminal. In a second terminal, activate the environment and run the saved capability:

```bash
source .venv/bin/activate
python -m bankops.replay.cli \
  --artifact evidence/artifacts/ledgerdesk-member-savings-balance.v1.json \
  --input member_id=M-10001
```

The structured result has status `success`, completes all six recorded steps, and returns `$4,250.75`. No LLM is called during replay.

To write value-free JSONL action events and capture the UI if replay fails:

```bash
python -m bankops.replay.cli \
  --artifact evidence/artifacts/ledgerdesk-member-savings-balance.v1.json \
  --input member_id=M-10001 \
  --log evidence/replay/local-run.jsonl \
  --failure-screenshot evidence/replay/local-failure.png
```

The log stores input and output field names for debugging, never their values. A screenshot is written only when replay returns `failure`.

Run the exceptional business outcome:

```bash
python -m bankops.replay.cli \
  --artifact evidence/artifacts/ledgerdesk-member-savings-balance.v1.json \
  --input member_id=M-99999
```

This returns `business_outcome` with code `member_not_found` after the search step, without attempting to open a member record. Redacted evidence from both verified runs is stored under `evidence/replay/`.

## Development checks

```bash
ruff format --check .
ruff check .
mypy
pytest
```

The genuine LLM-discovery command will be added when that milestone is implemented.
