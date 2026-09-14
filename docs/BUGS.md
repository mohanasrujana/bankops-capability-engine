# Bug Log

Only issues affecting behavior, correctness, safety, maintainability, developer workflow, or submission quality belong here. Routine formatting cleanup does not require a bug entry.

## BUG-001: Quality gate passed while an intended test file was missing

- **Status:** Fixed
- **Discovered:** 2026-09-10
- **Severity:** Verification gap
- **Symptom:** `pytest` passed with two tests even though four intended LedgerDesk domain tests had not been created.
- **Cause:** Test runners validate discovered tests; they do not know which additional tests the developer intended to create.
- **Impact:** The domain implementation appeared green without direct behavioral coverage.
- **Fix:** Added `tests/unit/test_ledgerdesk_domain.py`, confirmed all six expected tests were collected, and reran the full quality gate.
- **Prevention:** Verify collected test names or counts at checkpoints and add coverage checks for critical modules.
- **Evidence:** `pytest --collect-only` listed all six expected tests, and the full suite passed with six tests.

## BUG-002: Starlette TestClient emits an AnyIO deprecation warning

- **Status:** Mitigated
- **Discovered:** 2026-09-10
- **Severity:** Dependency compatibility warning
- **Symptom:** The passing health-endpoint test emits a warning that `anyio.abc.BlockingPortal` is deprecated.
- **Cause:** Starlette 1.6.0 references a deprecated alias provided by AnyIO 4.15.1 inside `starlette.testclient`.
- **Impact:** Application behavior is unaffected, but noisy test output can hide future actionable warnings.
- **Fix:** Added an exact pytest filter matching only the dependency module, warning category, and message.
- **Prevention:** Keep exact dependency versions recorded and review or remove the filter when Starlette updates the reference.
- **Evidence:** All seven tests passed without a warnings summary; Ruff and strict mypy also passed.
