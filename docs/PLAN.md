# Implementation Plan

## Product boundary

BankOps Capability Engine is the automation system. LedgerDesk is the synthetic legacy banking application it operates. The primary goal is to look up a synthetic member, open account details, return the savings balance, and verify completion.

## End-to-end lifecycle

1. Accept a goal and target.
2. Use an LLM-driven observe-decide-act loop against LedgerDesk.
3. Enforce policy before each proposed action.
4. Record success as a typed, versioned capability artifact.
5. Replay the artifact deterministically without LLM decisions.
6. Return structured success, business outcome, intervention, or failure.
7. Transfer the same live session to a human when required.
8. Preserve logs, screenshots or traces, and results as evidence.

## Technology

- Python
- FastAPI and Jinja2 for LedgerDesk
- Pydantic for validated contracts
- Playwright for browser control
- OpenAI Python SDK for discovery
- pytest, Ruff, and mypy for verification

## Phases

1. Python foundation and clean Python-first history
2. LedgerDesk live member-lookup flow and controlled outcomes
3. Artifact and result contracts
4. Deterministic replay through a `SurfaceAdapter`
5. Safety, redaction, and evidence
6. Genuine LLM discovery
7. Same-session human handoff
8. Submission evidence and documentation audit

## Deliberate cuts

- Real bank systems or data
- Desktop automation implementation
- Production authentication or multi-tenancy
- Distributed execution infrastructure
- Full real-time co-browsing UI
- Unlimited LLM recovery during replay

These remain design extensions, not implementation claims.
