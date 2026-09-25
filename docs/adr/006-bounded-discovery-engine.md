# ADR-006: Caller-owned discovery criteria and bounded orchestration

Status: Accepted
Date: 2026-09-24

## Context

The provider can return well-typed proposals but cannot decide its own permissions
or establish task success. The collector and surface adapter already separate
perception from execution. This checkpoint connects them through a bounded loop.

## Decision

`DiscoveryContract` comes from the trusted caller and contains execution policy,
expected output names, a success checkpoint, and optional business outcomes.
The provider receives expected output names and the caller checkpoint as context.
Each iteration observes, requests one decision, refreshes the observation, checks
policy, obtains authorization, verifies the observation has not changed during
authorization, executes at most one action, and observes again.

All actions require an explicit true response from an injected `ActionAuthorizer`;
the absence of one denies action execution. This trusted component must assess
the action's actual target, side effects, and extraction source independently of
the model's risk label. Irreversible proposals are always rejected. The current
checkpoint defines the interface but supplies no production authorizer.

Fill/click targets must match current observed controls. Disabled controls are
blocked; fills also reject readonly and password controls. Fill values must be
complete references to declared inputs, keeping recorded steps parameterized.
Unknown or repeated output names and duplicate completed step IDs are rejected.
Wait/extraction retry declarations are rejected in discovery; replay's existing
recovery remains separate.

A success proposal requires all expected outputs and successful verification of
both trusted and proposed checkpoints. The authorizer remains responsible for
validating extraction sources: the engine does not infer whether an arbitrary
string satisfies the natural-language goal. Model-reported business outcomes
require a matching caller-declared checkpoint. Raw model stop messages and
exception details are not copied into result error codes.

## Bounds and ownership

`max_steps` counts model decisions, including a completion or stop proposal.
Exhausting it returns `max_steps` without another model call. One asynchronous
deadline wraps navigation, observations, provider calls, authorization, actions,
and completion checks. External cancellation propagates. A cancelled action may
already have affected the page; incomplete actions are not recorded as completed
or retried. The caller retains the live browser session on every outcome.

The result retains completed actions and outputs for later artifact emission.
It is not redacted evidence and must not be directly logged as such.

## URL checks and limitations

Require exact scheme/authority and path boundaries when comparing current URLs
to caller scopes. Reject credentials and decoded dot segments. Check the entry
URL before navigation, and observed URLs before giving page content to the model
or executing another action. A refreshed observation detects changed state during
authorization, but cannot make a browser action atomic with that check.

These checks detect navigation outside scope after it occurs; they do not prevent
cross-origin requests, redirects, popup creation, or side effects of a click.
Browser navigation safeguards and a LedgerDesk-specific authorizer are necessary
before enabling a live model-driven command. Truncated observations also cannot
prove that all page state stayed unchanged.

## Alternatives and verification

Trusting model risk labels or model-selected completion criteria would allow
proposals to grant their own authority. Reusing the deterministic replay loop
directly would mix fixed artifact execution with iterative model decisions.
Separate orchestration retains the shared action and surface contracts while
keeping these responsibilities explicit.

Tests cover authorization, current-control checks, target/action scopes, input
references, output completeness, independent checkpoints, stop outcomes, budgets,
failure sanitization, and cancellation. A real Chromium test uses a scripted
provider and routed HTTP fixture to fill, click, extract, and verify. This proves
integration, not live model behavior, API schema acceptance, artifact generation,
or genuine discovery evidence.
