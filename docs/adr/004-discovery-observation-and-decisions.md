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

## Collector checkpoint

`PlaywrightObservationCollector` owns perception separately from the replay
adapter so deterministic execution does not acquire a discovery dependency.
One browser evaluation captures URL, title, and rendered main-document body text.
It returns only the bounded strings, using Unicode code points to match Python
length validation. The browser still computes the full text before slicing;
this is a model-input/transfer bound, not a DOM memory bound.

A five-second asynchronous deadline prevents waiting indefinitely on observation;
the future loop must also enforce its remaining overall time budget. Collection
does not navigate, retry, or change the page. It excludes ordinary hidden content
through rendered-text semantics, but is not a sensitive-data redaction mechanism.
It does not cover iframe documents or provide accessible control metadata yet.
Real-browser tests exercise behavior on routed HTTP fixtures without requiring
an external website or model API key.

## Structured native controls checkpoint

Observations now carry up to 100 rendered native inputs, textareas, selects,
buttons, and links, each with a tag, input type, name hint, disabled/readonly
flags, and a locator plan. Name hints use label references, ARIA labels,
associated labels, button/link text, then placeholders, bounded to 500 Unicode
characters. Truncation of either names or the control list marks the observation
as truncated. Input values are not directly read into control metadata. This
does not guarantee redaction: labels, text, and other page content may contain
sensitive information.

Use structural CSS paths, capped at 4096 characters, rather than treating a
heuristic name hint as a verified accessible name. Overlong paths are omitted
and mark the observation truncated. Paths avoid collisions between duplicate
labels and can be executed by the existing adapter; they can become stale after
DOM changes. Future artifact emission should prefer verified semantic locators
where available. This checkpoint does not claim durable selectors or implement
the full accessible-name algorithm, custom ARIA widgets, shadow DOM, or frames.

Disabled and readonly metadata informs a future decision provider; it does not
authorize an action. The adapter and execution policy must still check a proposed
action against current state. Tests demonstrate actual fill/click operations
using collected targets and confirm duplicate-name targets remain distinct.
