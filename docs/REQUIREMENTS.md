# Assignment Requirements

Each requirement has a stable ID so code, tests, evidence, and documentation can refer to it precisely. A requirement is checked only after verification evidence exists.

## Discovery

- [ ] **DISC-01:** Accept a natural-language goal and target application.
- [ ] **DISC-02:** Run a real LLM-driven observe-decide-act loop.
- [ ] **DISC-03:** Interact with a live UI by clicking, typing, navigating, and reading state.
- [ ] **DISC-04:** Stop on success, maximum steps, timeout, or dead end.
- [ ] **DISC-05:** Preserve evidence from at least one genuine LLM-driven run.

## Capability artifact

- [ ] **ART-01:** Emit a typed and serializable artifact after successful discovery.
- [ ] **ART-02:** Record ordered actions independently of the raw LLM transcript.
- [ ] **ART-03:** Represent robust target locators.
- [ ] **ART-04:** Declare typed input parameters.
- [ ] **ART-05:** Declare typed outputs and extraction rules.
- [ ] **ART-06:** Include a checkpoint or success condition.
- [ ] **ART-07:** Version artifacts for human review and future migration.

## Deterministic replay

- [ ] **REP-01:** Replay a saved artifact without LLM decision-making.
- [ ] **REP-02:** Substitute invocation parameters safely.
- [ ] **REP-03:** Wait for and verify expected UI states.
- [ ] **REP-04:** Verify the final checkpoint.
- [ ] **REP-05:** Return declared outputs in a structured result.

## Errors and outcomes

- [ ] **ERR-01:** Represent successful completion separately from errors.
- [ ] **ERR-02:** Represent expected business outcomes such as "member not found."
- [ ] **ERR-03:** Detect and retry explicitly recoverable conditions.
- [ ] **ERR-04:** Stop with debuggable context on hard failures.
- [ ] **ERR-05:** Identify the failed step, expectation, and observation.

## Safety

- [ ] **SAFE-01:** Enforce an allowlist of permitted targets and actions.
- [ ] **SAFE-02:** Classify safe, reversible, risky, and irreversible actions.
- [ ] **SAFE-03:** Block or require confirmation for risky actions.
- [ ] **SAFE-04:** Keep credentials, tokens, and raw sensitive data out of artifacts.
- [ ] **SAFE-05:** Redact sensitive values from logs.

## Observability

- [ ] **OBS-01:** Produce structured logs of actions and decisions.
- [ ] **OBS-02:** Capture a screenshot, trace, or equivalent rich signal on failure.
- [ ] **OBS-03:** Generate evidence for discovery and replay runs.

## Human handoff

- [ ] **HITL-01:** Detect when discovery or replay requires human intervention.
- [ ] **HITL-02:** Create an intervention request containing actionable context.
- [ ] **HITL-03:** Pause automation without closing the live session.
- [ ] **HITL-04:** Allow a human to control that same session.
- [ ] **HITL-05:** Record the human's actions.
- [ ] **HITL-06:** Transfer control back and resume or complete the run.

## Extensibility design

- [ ] **EXT-01:** Separate surface-specific perception and actions from artifact semantics.
- [ ] **EXT-02:** Explain extension to legacy web and desktop applications.
- [ ] **EXT-03:** Explain artifact reuse across tenants using the same vendor application.
- [ ] **EXT-04:** Explain tenant-specific overrides and version drift detection.

## Deliverables

- [ ] **DEL-01:** Publish the source in a public Git repository.
- [ ] **DEL-02:** Provide setup and exact demo commands in `/README.md`.
- [ ] **DEL-03:** Provide `/REPORT.md` using the seven required headings.
- [ ] **DEL-04:** Store a saved example artifact under `/evidence/`.
- [ ] **DEL-05:** Store discovery and replay logs under `/evidence/`.
- [ ] **DEL-06:** Demonstrate at least one exceptional replay outcome.
- [ ] **DEL-07:** Keep secrets and real PII out of the repository.
