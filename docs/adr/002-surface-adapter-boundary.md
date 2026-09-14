# ADR-002: Keep deterministic replay independent of UI technology

- Status: Accepted
- Date: 2026-09-14

## Context

The assignment requires reusable deterministic replay and asks how the design extends across modern web, legacy web, and desktop surfaces. Browser-specific calls embedded directly in replay would couple artifact semantics to Playwright and make both unit testing and future surface support harder.

## Decision

`ReplayEngine` interprets validated capability artifacts and returns typed results. It depends on a narrow asynchronous `SurfaceAdapter` protocol for navigation, fill, click, wait, extraction, and checkpoint operations.

The replay engine owns:

- invocation validation and template binding;
- deterministic step order;
- business-outcome detection;
- success-checkpoint enforcement;
- structured result and error construction.

Each surface adapter owns:

- translating locator plans into surface-native selectors;
- performing UI operations;
- observing checkpoints;
- reporting surface failures without changing workflow meaning.

## Alternatives considered

### Call Playwright directly from replay

This is initially shorter, but browser details would spread through the orchestration logic and make isolated tests dependent on a live browser.

### Put workflow decisions inside each adapter

This would support different surfaces, but each adapter could interpret the same artifact differently and weaken deterministic behavior.

## Consequences

- Core replay can be tested quickly with a fake surface.
- Playwright remains the first real adapter rather than becoming the system architecture.
- A future desktop adapter can preserve artifact meaning while changing its interaction mechanism.
- Adapter contract changes must be reviewed because every surface implementation depends on them.
