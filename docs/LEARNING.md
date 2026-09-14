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

## POST for member search

- GET form values appear in URLs and are commonly retained in browser, proxy, and access logs.
- POST moves the member identifier into the request body, reducing accidental URL exposure.
- POST alone is not sufficient protection; later logging policy must still redact sensitive request values.

## Business outcome versus failure

- A well-formed unknown member ID returns HTTP 200 with `Member Not Found` because the application processed the request successfully.
- A malformed identifier returns HTTP 400 because it violates the request contract.
- This distinction will later map directly into replay's structured result taxonomy.

## Opaque record identifiers

- POST keeps the searched member ID out of the query string, but linking to `/members/M-10001` would expose it again.
- LedgerDesk therefore links through a separate opaque record ID such as `rec-a7f3c2`.
- Unknown record pages do not reflect the requested identifier into HTML, limiting accidental disclosure.

## Currency representation

- Savings balances remain integer cents in the domain model.
- Display formatting uses integer division and remainder rather than floating-point arithmetic.
- This preserves exact values while still rendering a human-friendly amount such as `$4,250.75`.
