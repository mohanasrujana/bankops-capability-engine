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

## Dependency inversion through a surface adapter

- The replay engine understands workflow semantics but does not import Playwright.
- A `SurfaceAdapter` protocol states the operations replay needs without dictating how a browser or desktop tool performs them.
- A fake adapter makes orchestration tests fast and deterministic; the real Playwright adapter will separately prove browser behavior.
- This is dependency inversion: the high-level replay policy defines the interface, and low-level UI technology implements it.

## URL allowlisting

- Raw `startswith` URL checks are unsafe because an attacker-controlled hostname can begin with trusted-looking text.
- Replay parses the URL and compares scheme and network location before checking the permitted path prefix.
- Rejected entrypoints fail before navigation, which keeps the unsafe request outside the surface boundary.

## Playwright locator fallback

- The adapter attempts locator candidates in artifact order and stops at the first successful operation.
- Accessibility-based roles and labels are preferred because they describe user-visible intent; CSS remains useful for structurally stable legacy markup.
- Playwright exceptions are translated into `SurfaceError`, keeping library-specific errors outside replay semantics.
- A missing checkpoint is an observed false condition, while an invalid checkpoint pattern is a malformed instruction; those cases must not be conflated.

## Coordinate safety

- A coordinate has meaning only relative to the viewport in which it was recorded.
- The adapter refuses a coordinate click if the current viewport is absent or differs from the recorded dimensions.
- It also verifies that the point lies inside those dimensions, preferring a safe failure over an unintended click.

## Deterministic replay evidence

- “No LLM during replay” means every decision comes from the validated artifact and replay code; the browser run does not call the OpenAI SDK.
- A business outcome is not a failed automation: the UI reached a declared, expected state and replay returned its stable outcome code.
- Completed step IDs prove where execution stopped. The not-found run contains only fill and search, demonstrating that later actions were not attempted.
- Redaction follows artifact metadata rather than hard-coded field names, so newly declared sensitive inputs and outputs receive the same protection.
- Runtime output may show synthetic demo data, while saved evidence retains the structural proof with sensitive-designated values removed.

## Structured observability without data leakage

- A useful action log needs stable identifiers and ordering more than raw field values.
- Run IDs group events, while contiguous sequence numbers reconstruct exact execution order without relying only on timestamps.
- Step IDs and action kinds explain what happened; input and output names explain data flow; the corresponding values remain absent.
- Failure screenshots complement structured events because they preserve unexpected UI state that a step ID alone cannot describe.
- Typed event fields prevent accidental schema drift and make logging code subject to the same strict checks as replay code.

## Bounded recovery

- A timeout does not prove an action failed; it may mean the response was slow after the action succeeded.
- Repeating clicks can therefore duplicate a submission, while repeating a wait or read is observation-like and safer.
- Recovery policy belongs in the artifact so reviewers can see it and replay does not invent behavior dynamically.
- Attempt and delay limits prevent transient recovery from becoming an unbounded loop.

## Approval as a control state

- `intervention_required` is neither success nor failure: automation intentionally stopped before a risky operation.
- The approval request contains actionable metadata without input values.
- Deny-by-default means the absence of an approval mechanism cannot accidentally become permission.
- This typed request will become the bridge to same-session human handoff later.
