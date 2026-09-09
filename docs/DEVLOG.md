# Development Log

## 2026-09-10 — Product and architecture foundation

### Completed

- Defined BankOps Capability Engine as the automation system and LedgerDesk as its synthetic target.
- Mapped the assignment to stable requirement IDs.
- Accepted a Python modular-monolith architecture.
- Agreed on discovery/replay separation, artifact shape, result taxonomy, locator order, safety rules, handoff states, evidence, tests, cut lines, and build phases.

## 2026-09-10 — Python foundation

### Completed

- Created an isolated Python 3.13.5 virtual environment.
- Added PEP 621 metadata and dependencies in `pyproject.toml`.
- Configured pytest, Ruff, and strict mypy.
- Created separate BankOps, LedgerDesk, and layered test packages.
- Implemented project identity and runtime-validated synthetic member lookup.

### Verification

- Dependency consistency and all runtime imports passed.
- Ruff formatting and linting passed.
- Strict mypy passed.
- All six expected pytest tests were collected and passed.

### Next

- Captured exact resolved dependencies in `requirements.lock`.
- Reverified dependency consistency, Ruff, mypy, six pytest tests, and whitespace checks.
- The repository is ready for the reviewed Python-first root commit.
- Build the LedgerDesk HTTP and HTML workflow.
