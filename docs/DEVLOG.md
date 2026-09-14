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
- Created and pushed Python-first root commit `c32947c`.
- Build the LedgerDesk HTTP and HTML workflow.

## 2026-09-10 — LedgerDesk application shell

### Completed

- Added a FastAPI application factory and typed health endpoint.
- Added a Jinja2-rendered legacy-style member-search page.
- Preserved semantic labels, headings, and button text without relying on test IDs.
- Added HTTP integration tests for health and rendered form contracts.

### Verification

- Ruff formatting and linting passed.
- Strict mypy passed.
- All eight pytest tests passed.

## 2026-09-11 — LedgerDesk search outcomes

### Completed

- Changed member search from GET to POST so synthetic member identifiers do not appear in URLs or ordinary access logs.
- Added form parsing through `python-multipart` and refreshed the exact dependency lock.
- Implemented found, not-found, and invalid-input render branches.
- Kept the savings balance off the search result so the demonstration remains a multistep flow.

### Verification

- Known-member search returns an Open Member link.
- Unknown-member search returns HTTP 200 as a business outcome.
- Malformed identifiers return HTTP 400.
- Ruff formatting and linting, strict mypy, all eleven tests, and whitespace checks passed.

## 2026-09-13 — LedgerDesk member details

### Completed

- Added opaque record IDs so detail-page URLs do not expose member IDs.
- Added record lookup independent of the member-search identifier.
- Added integer-cents currency formatting.
- Added separate member-detail and safe record-not-found pages.
- Exposed the savings balance only after the Open Member navigation step.

### Verification

- Found-result links use opaque record IDs and exclude member IDs from `href` values.
- The detail page renders `$4,250.75` with an accessible Savings Balance label.
- Unknown record IDs return HTTP 404 without reflecting the supplied record value.
- Ruff, strict mypy, all sixteen tests, and whitespace checks passed.

## 2026-09-13 — Real-browser verification

### Completed

- Installed the Chromium runtime matching the locked Playwright package.
- Ran the success and member-not-found workflows against a live Uvicorn server.
- Added local setup, server, manual demo, and quality-check commands to README.

### Verification

- Success flow: Search `M-10001` → Open Member → Member Details → `$4,250.75`.
- Business outcome: Search `M-99999` → Member Not Found with no Open Member link.
- Browser console reported no errors.
- Server logs showed expected GET/POST/GET requests with HTTP 200 responses.
- Screenshot review showed a readable legacy layout without clipping or overlap.
