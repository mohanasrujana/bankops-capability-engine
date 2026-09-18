# ADR-003: Use conservative recovery and explicit risky-action approval

- Status: Accepted
- Date: 2026-09-18

## Context

Transient UI timing failures should not immediately fail every replay, but blindly repeating actions can duplicate state changes. Risky operations also require a clear control boundary before execution.

## Decision

Automatic retry is available only on `wait_for` and `extract` steps. A capability must explicitly record a retry policy with two or three total attempts and a delay of at most two seconds. Fill and click steps are not automatically retried.

Before a `risky` step executes, replay creates a typed approval request containing the capability ID, step ID, action kind, risk, and description. An approval provider must affirmatively approve it. Without approval, replay returns `intervention_required` before executing that step. Irreversible actions remain prohibited in reusable artifacts.

## Alternatives considered

### Retry every failed step

This is simpler but can duplicate submissions or activate a control twice when the first response was merely slow.

### Retry nothing

This is safest for state changes but unnecessarily fails on short-lived visibility and extraction timing issues.

### Treat missing approval as a failure

This loses the important distinction between broken automation and a workflow intentionally paused for human authorization.

## Consequences

- Recovery is bounded, reviewable, and part of the artifact rather than hidden engine behavior.
- Business-changing actions are never repeated automatically.
- Risky work becomes an intervention state that the later same-session handoff controller can present to a human.
- Approval-provider failures and richer approval UX remain future extensions.
