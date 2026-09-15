# BankOps Capability Engine — Design Report

This report evolves alongside the implementation. Claims will be finalized only after the corresponding behavior and evidence are verified.

## 1. Architecture

The planned system is a Python modular monolith with explicit discovery, artifact, replay, safety, evidence, handoff, and surface boundaries. It operates LedgerDesk through a Playwright adapter. The LLM participates only in discovery; replay consumes a typed Pydantic artifact without model decisions.

## 2. Artifact schema

Artifact models are immutable and reject unknown fields. Locator plans contain one or more discriminator-based candidates covering role, label, visible text, CSS, and coordinates. A coordinate locator can appear only once and only as the final fallback. The versioned artifact declares typed inputs and outputs, compatibility metadata, bounded actions, business outcomes, a success checkpoint, and execution policy. Cross-field validation rejects duplicate IDs, undeclared template inputs, incomplete or duplicate extraction mappings, disallowed action kinds, irreversible actions, and risky actions without an approval requirement.

The repository includes a validated, hand-reviewed LedgerDesk seed artifact for the member-savings workflow. It is intentionally identified as replay input rather than claimed as LLM discovery evidence; the genuine discovery run will emit the same schema later.

## 3. Determinism & error handling

The surface-independent replay engine validates invocation inputs, binds declared parameters, enforces an origin-aware URL allowlist, executes the artifact's bounded ordered steps, checks declared business outcomes, verifies the final checkpoint, and returns typed `success`, `business_outcome`, `intervention_required`, or `failure` results. Failures retain completed steps, the failed step ID, and expected-versus-observed context. The core has no LLM dependency. A Playwright adapter now implements ordered semantic and CSS locator fallback, bounded UI operations, extraction, checkpoints, and viewport-validated coordinate clicks; end-to-end saved-artifact replay is the next evidence gate.

## 4. Heterogeneity & multi-tenant

`SurfaceAdapter` separates semantic actions from browser execution, and the Playwright implementation proves the boundary against Chromium. Application-family metadata and planned tenant-specific overrides allow reuse without claiming that desktop or production multi-tenant infrastructure is implemented.

## 5. Escalation & handoff

The planned controller transitions through `AUTOMATION`, `WAITING_FOR_HUMAN`, and `HUMAN` while preserving the same Playwright browser context. Verified details will be added after demonstration.

## 6. Safety

The planned policy layer allowlists targets and actions, classifies risk, requires approval for risky steps, blocks irreversible demo actions, and redacts sensitive values. LedgerDesk uses synthetic data only.

## 7. Cuts

The initial slice excludes real bank integration, desktop control, production authentication, distributed queues, production multi-tenancy, a full co-browsing console, and unlimited LLM recovery.
