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
