# Learning Notes

## System versus target

- BankOps Capability Engine is the automation system.
- LedgerDesk is the synthetic banking interface it operates.

## Discovery versus replay

- Discovery uses an LLM because the path is initially unknown.
- A successful run becomes a typed capability artifact.
- Replay follows that artifact without LLM decisions.

## Familiar foundation, focused learning

- Python is the familiar implementation language.
- Jinja2 renders LedgerDesk HTML.
- Playwright observes and controls the browser.
- New libraries are introduced through small tests before becoming architectural dependencies.

## Verification rule

- Code being present is not proof that behavior works.
- Each checkpoint defines an expected result and failure signal.
- Features are complete only after relevant checks and evidence pass.
