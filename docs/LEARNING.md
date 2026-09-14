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

## Discriminated unions

- Every locator contains a `kind` such as `role`, `label`, `css`, or `coordinate`.
- Pydantic uses that discriminator to select the correct model and validation rules.
- This is safer than one model containing many unrelated optional fields.

## Strict artifact models

- `extra="forbid"` rejects misspelled or invented fields instead of ignoring them.
- `frozen=True` prevents a validated contract from being mutated accidentally.
- Coordinate targeting is allowed only as one final fallback because it is the least stable targeting strategy.

## Cross-field contract validation

- Field validation answers questions such as “is this timeout within bounds?”
- Cross-field validation answers questions such as “does this fill step reference an input the artifact actually declares?”
- An output declaration alone does not produce a value, so each declared output must map to exactly one extraction step.
- The action allowlist is stored with the artifact and checked against every step, making its execution envelope explicit during review.
- Irreversible actions are excluded from reusable artifacts; risky actions must advertise an approval requirement before replay can accept the contract.

## Seed artifact versus discovered artifact

- A seed artifact is deliberately authored from a known, reviewed workflow so replay can be built and tested independently.
- A discovered artifact is emitted after an LLM observes and successfully operates the live UI.
- Both use exactly the same schema, but only the second proves the assignment's discovery requirement.
- Keeping these claims separate lets us develop replay before spending model calls while preserving honest evidence boundaries.
