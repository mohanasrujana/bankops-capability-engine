# Project Status

Last updated: 2026-09-14

## Current milestone

M1 — Define the reusable capability contract

## Done

- Read the assignment and mapped it to stable acceptance-criteria IDs.
- Named the product BankOps Capability Engine and its synthetic banking surface LedgerDesk.
- Agreed on the modular architecture, target workflow, outcome taxonomy, locator strategy, safety model, evidence plan, scope cuts, and build order.
- Accepted ADR-001: a Python modular monolith, with Jinja2 and Playwright as focused learning areas.
- Kept the existing GitHub repository and remote.
- Published the verified Python-first root commit `c32947c` to `origin/main`.
- Created and verified a project-local Python 3.13.5 virtual environment and Git ignore rules.
- Created importable package boundaries for BankOps, LedgerDesk, and layered tests.
- Added and parsed `pyproject.toml` with Python dependencies and pytest, Ruff, and mypy policy.
- Recreated the project-identity behavior in Python and passed the complete Python quality gate.
- Recreated and tested LedgerDesk member lookup in Python with found, not-found, invalid-input, and whitespace-normalization cases.
- Added and tested LedgerDesk's FastAPI application factory and health endpoint.
- Rendered and tested LedgerDesk's legacy-style member-search page with Jinja2.
- Implemented and tested POST-based member search with found, not-found, and invalid-input views.
- Implemented and tested a separate member-detail page that displays the formatted savings balance.
- Replaced member IDs in detail URLs with opaque LedgerDesk record identifiers.
- Verified the complete LedgerDesk success and not-found flows in Chromium through Playwright.
- Implemented strict typed locator candidates and ordered locator plans for capability artifacts.
- Implemented typed actions, inputs, outputs, business outcomes, compatibility metadata, checkpoints, versioning, and execution policy.
- Added cross-field validation for unique identifiers, declared input references, complete output extraction, action allowlisting, and risk constraints.
- Saved and contract-validated the first LedgerDesk member-savings capability artifact under `evidence/artifacts/`.
- Recreated the project-identity behavior in Python and passed formatting, linting, strict typing, and two tests.
- Installed and verified the Python runtime/development dependencies in the isolated environment.

## Next

- Build deterministic replay against the reviewed LedgerDesk artifact.

## Blocked

- No current blocker for local Python development.
- A genuine discovery run will eventually require a model API key.

## Evidence

- Local repository: `/Users/satyasrujanapilli/Downloads/bankops-capability-engine`.
- Git remote: `https://github.com/mohanasrujana/bankops-capability-engine.git`.
- Local `main` and `origin/main` both point to LedgerDesk-flow commit `b13fe41`; the capability-contract work is not yet committed.
- Python baseline evidence: dependency validation, Ruff formatting and lint, strict mypy, and six pytest tests passed.
- LedgerDesk domain evidence: all six expected Python tests were collected and passed.
- LedgerDesk health-endpoint evidence: seven total tests passed; the known Starlette/AnyIO warning is narrowly mitigated and documented.
- Member-search page evidence: eight total tests passed with Ruff and mypy checks.
- Member-search outcome evidence: eleven total tests passed with Ruff, mypy, and whitespace checks.
- Complete HTTP-flow evidence: sixteen tests passed for search, result navigation, detail extraction, safe record lookup, and currency formatting.
- Browser evidence: success reached Member Details with `$4,250.75`, not-found rendered without an Open Member link, console errors were empty, and the legacy layout had no visible clipping or overlap.
- Locator-schema evidence: 21 total tests passed, including discriminator parsing, unknown-field rejection, and coordinate-fallback constraints.
- Capability-contract evidence: 32 intended tests were collected and passed, including action parsing and cross-field safety checks.
- Saved-artifact evidence: 33 intended tests passed, including loading the repository JSON through the production Pydantic contract.
- `pip check` reported no broken requirements; FastAPI, Jinja2, OpenAI, Playwright, Pydantic, and Uvicorn imported successfully.

## Working agreement

- Work proceeds in small, verifiable checkpoints.
- Learning-critical implementation is performed by the author with explanation and review from Codex.
- Codex may update documentation directly and report the changes afterward.
- Every material design choice records its rationale and alternatives.
- Material bugs record symptoms, cause, fix, prevention, and evidence.
- A feature is not complete without verification evidence.
- Planned work is never described as implemented work.
- Codex identifies meaningful commit boundaries and supplies review and commit commands.
