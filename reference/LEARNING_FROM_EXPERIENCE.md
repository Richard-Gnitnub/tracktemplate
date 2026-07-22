# Learning from Experience

Status: **append-only historical process ledger established on 2026-07-22.**

## Ledger rules

This document records durable adaptations learned from actual project work so
later development cycles do not repeat avoidable mistakes. It owns no live
phase status, requirement, risk state or acceptance decision. Those remain in
[PROJECT_PLAN.md](PROJECT_PLAN.md) and the applicable policy, contract or
open-phase evidence record.

Add a row only when an observation has evidence and led to a reusable process,
architecture or validation change. Link to the owning payload instead of
copying its technical detail. Do not edit an old row to make it match later
knowledge; append a correction or successor lesson.

## Experience ledger

| ID / date | Experience and evidence | Adaptation | Reusable rule |
| --- | --- | --- | --- |
| LFE-001 / Phase 0 | The legacy “Whole workflow” timing covered special-trackwork stages, not the whole product pipeline; see [BASELINE.md](BASELINE.md). | Benchmark scope, cache state and exclusions became explicit under [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md). | A persuasive label is not evidence of coverage; name exactly what ran. |
| LFE-002 / Phase 0 | A process exit code alone did not prove that FreeCAD executed assertions; see [VALIDATION.md](VALIDATION.md). | Headless tests gained explicit success sentinels and qualified-runtime checks. | Require positive evidence from inside the target host, not merely launcher success. |
| LFE-003 / Phase 0–1 | Repeated manual clicking, restarts and copied reports made workflow observation slow and inconsistent. | The development bridge introduced isolated profiles, deterministic recipes and copied fixtures; see [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md). | Automate repeatable observation, while keeping operator documents outside the experiment. |
| LFE-004 / Phase 1 | The macro contains shadowed definitions, aliases and runtime patches that make intuitive refactoring unsafe; see [PHASE1_INVENTORY.md](PHASE1_INVENTORY.md). | Static inventories, caller closures and frozen source anchors precede extraction. | Inventory the implementation that actually runs before choosing a module boundary. |
| LFE-005 / Phase 1 | Making a test pass can accidentally erase a real legacy invariant or defect witness. | [TESTING_POLICY.md](TESTING_POLICY.md) now separates implementation fixes from evidence-based oracle changes. | Change an oracle only when the oracle is wrong or the accepted requirement changed. |
| LFE-006 / Phase 1 | “Ordinary track” was used where the railway term is “plain line”, while some frozen identifiers could not safely be renamed. | [TERMINOLOGY.md](TERMINOLOGY.md) separates accepted terminology, review markers and frozen compatibility names. | Correct operator-facing language now; migrate persisted or evidence identifiers only with compatibility proof. |
| LFE-007 / Phase 1 | Software licence, engineering facts, reference data, media output and generated project output were being discussed as if they shared one rights boundary. | [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md) and [PROVENANCE.md](PROVENANCE.md) introduced source/value/dependency classification and fail-closed manifests. | Trace every output-affecting dependency; do not infer output rights from the software licence alone. |
| LFE-008 / Phase 1–2 | Updating every historical phase document after each tranche created bloat and contradictory “current” facts. | The documentation lifecycle in [AGENTS.md](../AGENTS.md) established one live plan, one open-phase evidence record and frozen accepted history. | Give each fact one live owner and link to it; history records what was known then. |
| LFE-009 / Phase 2–3 | Moving, cleaning and optimising code in one change would make parity failures difficult to diagnose. | [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md) requires mechanical extraction before cleanup or optimisation and names retirement gates. | Separate movement, behaviour change and performance claims into independently reviewable evidence. |
| LFE-010 / Phase 3–4 | Persisted derived geometry and cache results can become stale or compete with parametric intent. | [PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md) makes canonical intent authoritative and treats derived results as signed, discardable state. | Persist the smallest authoritative state; regenerate views and exact geometry at explicit boundaries. |
| LFE-011 / Phase 2–4 | Git, GitHub and system snapshots protect different failure modes and none alone protects ignored project data. | [RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md) separates checkpoint, system recovery, independent backup and restore proof. | Never call a protection layer a backup beyond the data and failure modes it actually covers. |
| LFE-012 / QA audit 2026-07-22 | Strong controls can still conflict, remain prose-only or lack a downstream owner. | [QUALITY_ASSURANCE.md](QUALITY_ASSURANCE.md) introduced explicit correction-or-gate disposition and an executable linkage check. | Every audit finding is corrected now or remains visibly open at a named phase gate. |

## Using the ledger

At the start of a materially similar tranche, review only the relevant rows
and follow their linked current controls. At phase close or a later formal QA
audit, append newly evidenced lessons; do not use this ledger as a checklist
substitute or a progress report.
