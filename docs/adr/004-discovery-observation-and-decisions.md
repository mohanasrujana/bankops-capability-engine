# ADR-004: Bounded observations and typed discovery proposals

Status: Accepted
Date: 2026-09-23

## Context

Discovery needs a representation of current browser state and a validated response
from a decision provider. This checkpoint defines contracts, not the provider,
browser collector, policy enforcement, or execution loop.

## Decision

Start with page URL, title, and visible text. Cap titles at 500 characters and
visible text at 20,000 characters, with a required truncation flag. These are
initial development bounds. The future collector must deliberately truncate and
set the flag; model validation rejects oversized observations rather than silently
cutting them. Empty pages remain representable for dead-end handling.

Use a discriminated union for one action proposal, a success proposal with a
checkpoint, or a non-success stop. Reuse the existing action/checkpoint types so
discovery and replay share semantics. The model cannot declare engine-owned
timeout or step-limit outcomes. A future engine must independently check policy,
input references, risk, outputs, and completion before accepting proposals.

## Alternatives and trade-offs

- Raw HTML provides richer details but consumes more context and includes hidden
  content. Bounded visible text is a smaller initial interface, but may not expose
  enough structure to identify controls. Collector work must evaluate this gap
  before live discovery; structured controls or screenshots can be added later.
- Unrestricted model commands offer flexibility but bypass existing action
  contracts. Typed proposals keep unsupported actions out of this boundary.
- Treating a model's success statement as final is simpler but lacks evidence.
  A proposed checkpoint still requires independent verification and output checks.

## Consequences

Observations and stop messages can contain sensitive values and untrusted page
content. They are not redacted evidence and must not be logged directly. Type
validation is not authorization or prompt-injection protection. Frozen models
are not deeply immutable. SDK structured-output compatibility will be checked
when the provider is implemented; these internal contracts make no such claim.
