# ADR 001: Python modular monolith with a local legacy-style target

- **Status:** Accepted
- **Date:** 2026-09-10

## Context

The assignment requires one complete vertical slice: LLM-driven discovery against a live UI, a typed reusable capability, deterministic replay, explicit outcomes and failures, safety controls, evidence, and same-session human handoff. The design must preserve credible seams for legacy web, desktop surfaces, and multi-tenant reuse without prematurely building distributed infrastructure.

## Decision

Build a Python modular monolith with these boundaries:

1. LedgerDesk, a synthetic legacy-style banking application, provides the safe live target.
2. FastAPI and Jinja2 serve LedgerDesk.
3. Playwright for Python implements the first browser `SurfaceAdapter`.
4. An LLM-driven loop chooses bounded typed actions during discovery only.
5. A recorder converts successful actions into versioned Pydantic capability artifacts.
6. A deterministic engine replays artifacts without LLM decisions.
7. Safety, structured logging, error classification, and human handoff remain explicit modules.
8. The first slice runs locally without queues, clusters, or production multi-tenant infrastructure.

## Target workflow

The first capability accepts a synthetic member ID, searches for the member, opens account details, and returns the savings balance. LedgerDesk will provide repeatable success, not-found, invalid-input, transient, permission-denied, and human-approval scenarios. No real credentials or PII are used.

## Why Python

- It is a language the author can confidently explain, debug, and defend.
- Pydantic validates untrusted form, model, artifact, and invocation data at runtime.
- Playwright and the OpenAI SDK provide first-class Python interfaces.
- One language covers the target application, discovery, replay, policy, evidence, and tests.

## Surface abstraction

Artifacts describe semantic actions and locator plans without calling Playwright directly. A `SurfaceAdapter` translates observation and action requests to a concrete UI. Future adapters could target accessibility APIs, screenshot coordinates, or desktop automation while preserving the capability contract.

## Locator strategy

Artifacts store ordered locator candidates rather than one brittle selector. Replay prefers accessible role and name, form label, anchored visible text, and stable structural selectors. Coordinate targeting is a guarded last resort requiring stronger checkpoint validation.

## Consequences

### Benefits

- Every core requirement can be demonstrated locally end to end.
- Exceptional states are repeatable and testable.
- The solution remains small enough to review and defend.
- The surface boundary supports a credible heterogeneity story.

### Limitations

- A local browser target does not prove desktop integration.
- Synthetic failures do not cover every banking-system behavior.
- The handoff is a functional demonstration, not a production co-browsing console.
- Cross-tenant reuse is initially represented in contracts and design rather than deployed infrastructure.

## Alternatives considered

- **Public demo site:** rejected because terms, availability, and UI changes are outside project control.
- **Microservices and queues:** rejected because they add breadth without strengthening the central contracts.
- **Coordinate-only control:** rejected because deterministic replay would be unnecessarily fragile.
- **Raw transcript replay:** rejected because transcripts are not typed, stable, reviewable capability contracts.
