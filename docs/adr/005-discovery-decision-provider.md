# ADR-005: A bounded decision provider separate from execution

Status: Accepted
Date: 2026-09-24

## Context and decision

Discovery needs model decisions without coupling browser control to an SDK.
`DecisionProvider` accepts typed context: request, current observation, completed
actions, and extracted output names. It returns an existing `DiscoveryDecision`.
The OpenAI implementation owns one Responses API request; it never executes an
action or grants approval. The caller owns the client lifecycle and model choice.

Calls have a 30-second outer deadline and SDK timeout, no automatic retries,
and a 4096-token response cap. The future engine must impose its remaining total
deadline too. `store=False` is requested; this is not a claim of zero retention.
Only input names are sent from the request's input mapping, enabling parameter
references. Goal, observations, and history can still contain sensitive content
and are not saved as logs by this provider.

## Schema and failure handling

The official [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
requires an object root, required properties, closed objects, and supported
composition. Wrap the internal union in a decision envelope, convert its disjoint
tagged `oneOf` branches to `anyOf`, remove discriminator/default annotations,
and convert constants to singleton enums. Require all wire fields, including
fields with local defaults. Nullable fields remain nullable. Validate the model's
JSON against the original Pydantic contract after receipt.

This normalization is specific to the current decision schema, not a general
JSON Schema converter. Schema changes must be reviewed for API compatibility.
Tests inspect the wire request through installed OpenAI SDK 3.11.0 and the locked
httpx2 transport with mock responses; they do not prove service acceptance.

Incomplete responses, refusals, invalid decisions, SDK failures, and timeouts
produce stable provider errors without raw response text in the public message.
No fallback decision is invented. External cancellation is allowed to propagate.

## Alternatives and consequences

- Calling the SDK directly from the engine would make independent orchestration
  tests harder; the protocol supports scripted providers for those tests.
- Using raw JSON mode would lose the service-side schema constraint. Structured
  Outputs is used alongside local validation, not as an authorization mechanism.
- Passing raw input values would encourage literal recording; named references
  support later artifact parameterization.

The prompt treats page content as untrusted and asks for conservative proposals.
This is not execution-time policy enforcement or proof of task completion. The
next engine checkpoint must enforce target/action policy and verify outputs and
checkpoints. Live model testing, artifact emission, and discovery evidence remain
unfinished; no discovery requirement is marked complete here.
