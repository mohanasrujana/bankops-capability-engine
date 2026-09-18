# BankOps Capability Engine — Design Report

This report evolves alongside the implementation. Claims will be finalized only after the corresponding behavior and evidence are verified.

## 1. Architecture

The planned system is a Python modular monolith with explicit discovery, artifact, replay, safety, evidence, handoff, and surface boundaries. It operates LedgerDesk through a Playwright adapter. The LLM participates only in discovery; replay consumes a typed Pydantic artifact without model decisions.

## 2. Artifact schema

Artifact models are immutable and reject unknown fields. Locator plans contain one or more discriminator-based candidates covering role, label, visible text, CSS, and coordinates. A coordinate locator can appear only once and only as the final fallback. The versioned artifact declares typed inputs and outputs, compatibility metadata, bounded actions, business outcomes, a success checkpoint, and execution policy. Cross-field validation rejects duplicate IDs, undeclared template inputs, incomplete or duplicate extraction mappings, disallowed action kinds, irreversible actions, and risky actions without an approval requirement.

The repository includes a validated, hand-reviewed LedgerDesk seed artifact for the member-savings workflow. It is intentionally identified as replay input rather than claimed as LLM discovery evidence; the genuine discovery run will emit the same schema later.

## 3. Determinism & error handling

The surface-independent replay engine validates invocation inputs, binds declared parameters, enforces an origin-aware URL allowlist, executes the artifact's bounded ordered steps, checks declared business outcomes, verifies the final checkpoint, and returns typed `success`, `business_outcome`, `intervention_required`, or `failure` results. Failures retain completed steps, the failed step ID, and expected-versus-observed context. The core has no LLM dependency. The Playwright adapter implements ordered semantic and CSS locator fallback, bounded UI operations, extraction, checkpoints, and viewport-validated coordinate clicks. Live Chromium replay completed all six saved steps and returned the declared balance; a second run returned `member_not_found` after search without executing later actions.

Replay emits typed JSONL events with a run ID and contiguous sequence numbers around every step. Events contain field names and execution metadata but omit invocation and extracted values. CLI failures can capture a full-page screenshot before the browser session closes.

Recovery is explicit and bounded in the artifact: only wait and extraction steps can record two or three attempts. State-changing clicks are never blindly repeated. Risky steps require affirmative approval through a typed provider boundary; otherwise replay returns `intervention_required` with actionable step context before executing the operation.

## 4. Heterogeneity & multi-tenant

`SurfaceAdapter` separates semantic actions from browser execution, and the Playwright implementation proves the boundary against Chromium. Application-family metadata and planned tenant-specific overrides allow reuse without claiming that desktop or production multi-tenant infrastructure is implemented.

## 5. Escalation & handoff

Replay now detects risky steps and emits typed intervention requests rather than treating them as failures. The next handoff layer will transition between automation and human control while preserving the same Playwright browser context; that same-session control transfer is not yet implemented.

## 6. Safety

The artifact and replay layers allowlist action kinds and URL origins, classify risk, reject irreversible reusable actions, and require affirmative approval for risky steps. Replay evidence uses artifact sensitivity metadata to redact inputs and outputs, while structured logs exclude runtime values entirely. LedgerDesk uses synthetic data only.

## 7. Cuts

The initial slice excludes real bank integration, desktop control, production authentication, distributed queues, production multi-tenancy, a full co-browsing console, and unlimited LLM recovery.
