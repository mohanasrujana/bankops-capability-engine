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

## 2026-09-14 — Artifact locator contract

### Completed

- Added strict immutable locator models for role, label, text, CSS, and coordinates.
- Added discriminator-based parsing using the `kind` field.
- Added ordered locator plans with at least one candidate.
- Required coordinate targeting to be a single final fallback.

### Reasoning

- Semantic locators are easier to review and more robust than coordinates.
- CSS remains a constrained structural fallback for legacy surfaces.
- Coordinates remain representable for hostile surfaces but cannot silently outrank stronger evidence.
- Unknown fields are rejected so schema typos do not become ignored safety or replay instructions.

### Verification

- Ruff, strict mypy, all 21 tests, and whitespace checks passed.

## 2026-09-14 — Complete capability contract

### Completed

- Added a bounded replay vocabulary for fill, click, wait, and extract actions.
- Added typed input and output declarations, application compatibility, business outcomes, a final success checkpoint, schema and capability versions, and execution policy.
- Enforced unique names and step IDs across the artifact.
- Required fill templates to reference declared inputs and every declared output to have exactly one extraction step.
- Required policy allowlisting for every action, blocked irreversible actions, and required approval policy for risky actions.

### Design choices

- Replay actions are a small discriminated union rather than arbitrary browser code so they remain deterministic and auditable.
- Timeouts are bounded from 100 to 30,000 milliseconds so a malformed artifact cannot wait forever.
- Business outcomes have their own checkpoints so expected conditions such as member-not-found are distinct from automation failures.
- Artifact validation checks relationships between fields, because individually valid fields can still form an unsafe or unexecutable contract.

### Verification

- The first gate exposed one test import-order violation and two formatting differences; Ruff corrected these mechanical issues.
- All 32 intended tests were collected and passed before the final complete quality gate.

## 2026-09-14 — Saved LedgerDesk capability

### Completed

- Added `evidence/artifacts/ledgerdesk-member-savings-balance.v1.json`.
- Recorded the six-step success path: fill, search, wait for result, open member, wait for balance, and extract.
- Recorded member-not-found and invalid-member-ID as expected business outcomes.
- Marked the member ID and savings-balance output as sensitive metadata for the future redaction layer.
- Added an integration test that loads the repository artifact through `CapabilityArtifact` and checks its ordered steps and outcomes.

### Design choices

- The first artifact is a hand-reviewed seed based on the browser flow already verified in Chromium.
- It is valid replay input and deliverable evidence, but it is not presented as discovery output; ART-01 remains open until a genuine LLM run emits an artifact.
- Semantic role and label locators come first, with CSS used only as a structural fallback where helpful.
- Explicit wait steps make expected state transitions visible instead of depending only on implicit browser timing.

### Verification

- The JSON parsed through the strict production artifact contract.
- All 33 intended tests passed; Ruff identified and mechanically corrected one test import-grouping issue.

## 2026-09-14 — Deterministic replay core

### Completed

- Added typed replay statuses, outputs, and debuggable error details.
- Added invocation validation for required, unknown, and incorrectly typed values.
- Added exact template binding for declared artifact inputs.
- Added origin-aware entrypoint allowlisting rather than unsafe raw string-prefix trust.
- Added deterministic dispatch for fill, click, wait, and extract steps.
- Added business-outcome checks after each completed step and final success-checkpoint enforcement.
- Added a UI-independent asynchronous `SurfaceAdapter` protocol and accepted ADR-002.

### Verification

- Fake-surface tests prove ordered operations without browser or model decisions.
- Failure tests preserve completed steps, the failed step ID, expected state, and observed state.
- A malicious lookalike host such as `127.0.0.1:8000.evil.test` is rejected before navigation.
- All 39 intended tests, Ruff, strict mypy, and whitespace checks passed.

### Next

- Implement locator fallback and UI operations in the Playwright adapter.
- Verify success and member-not-found replay against live LedgerDesk.
