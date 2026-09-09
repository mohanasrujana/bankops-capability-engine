# BankOps Capability Engine — Design Report

This report evolves alongside the implementation. Claims will be finalized only after the corresponding behavior and evidence are verified.

## 1. Architecture

The planned system is a Python modular monolith with explicit discovery, artifact, replay, safety, evidence, handoff, and surface boundaries. It operates LedgerDesk through a Playwright adapter. The LLM participates only in discovery; replay consumes a typed Pydantic artifact without model decisions.

## 2. Artifact schema

The planned artifact declares identity, version, application compatibility, typed inputs and outputs, semantic actions, ordered locator candidates, bounded waits and retries, known outcomes, risk levels, and a final checkpoint. Details remain provisional until implemented and tested.

## 3. Determinism & error handling

Replay will validate artifacts and inputs, execute bounded steps, and return `success`, `business_outcome`, `intervention_required`, or `failure`. Recoverable conditions use bounded recorded recovery. Verified details will replace this plan after implementation.

## 4. Heterogeneity & multi-tenant

The planned `SurfaceAdapter` separates semantic actions from browser execution. Application-family metadata and tenant-specific overrides will allow reuse without claiming that desktop or production multi-tenant infrastructure is implemented.

## 5. Escalation & handoff

The planned controller transitions through `AUTOMATION`, `WAITING_FOR_HUMAN`, and `HUMAN` while preserving the same Playwright browser context. Verified details will be added after demonstration.

## 6. Safety

The planned policy layer allowlists targets and actions, classifies risk, requires approval for risky steps, blocks irreversible demo actions, and redacts sensitive values. LedgerDesk uses synthetic data only.

## 7. Cuts

The initial slice excludes real bank integration, desktop control, production authentication, distributed queues, production multi-tenancy, a full co-browsing console, and unlimited LLM recovery.
