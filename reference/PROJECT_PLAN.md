# Project Plan

Status: **Phase 4 complete — accepted 2026-07-28; Phase 5 is not started and
requires a separate project-owner opening decision.**

This file is the project dashboard. It owns only phase status, exit-condition
status, the live-risk summary, owner-decision summary and links to evidence.
Implementation detail belongs in
[current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md); detailed current risks
and decisions belong in the JSON registers beside it.

## Phase status

| Phase | Outcome | Exit status | State |
| ---: | --- | --- | --- |
| 0 | Recoverable baseline and benchmark checkpoint | 6/6 evidenced | Complete — accepted 2026-07-19 |
| 1 | Product, dependency, correctness and performance inventory | 9/9 evidenced | Complete — accepted 2026-07-22 |
| 2 | Minimal modular foundation and validation harness | 5/5 evidenced | Complete — accepted 2026-07-22 |
| 3 | First parity-proven vertical slice | 5/5 evidenced | Complete — accepted 2026-07-22 |
| 4 | Canonical state, signatures and persistence | 6/6 evidenced | Complete — accepted 2026-07-28 |
| 5 | Lightweight editing prototype and renderer decision | 0/4 evidenced | Not started — awaiting owner opening decision |
| 6 | Explicit exact-validation and export seam | 0/5 evidenced | Not started |
| 7 | Core alignment, station and multiple-track migration | 0/4 evidenced | Not started |
| 8 | Turnout, crossover and timbering migration | 0/4 evidenced | Not started |
| 9 | Chair definitions, assisted assimilation, production records and export completion | 0/9 evidenced | Not started |
| 10 | Workbench integration, launcher reduction and beta Addon packaging | 0/5 evidenced | Not started |
| 11 | Stabilisation and release-candidate qualification | 0/7 evidenced | Not started |

## Closed Phase 4 exit conditions

| Exit condition | Status | Evidence |
| --- | --- | --- |
| Selected-slice save/reopen without result or identity drift | Evidenced | [Final disposition](history/phase-closeouts/PHASE4_CLOSEOUT.md#current-phase-4-exit-condition-disposition) |
| Canonical analysis and Phase 4 derived-preview invalidation, including cold/reuse/change-back | Evidenced | [Final disposition](history/phase-closeouts/PHASE4_CLOSEOUT.md#current-phase-4-exit-condition-disposition) |
| Undo/Redo and failed updates leave a valid document | Evidenced | [Final disposition](history/phase-closeouts/PHASE4_CLOSEOUT.md#current-phase-4-exit-condition-disposition) |
| Renderer-neutral preview artifacts can be deleted and regenerated from canonical state | Evidenced | [Final disposition](history/phase-closeouts/PHASE4_CLOSEOUT.md#current-phase-4-exit-condition-disposition) |
| Deterministic, fail-closed chair-definition package | Evidenced | [Final disposition](history/phase-closeouts/PHASE4_CLOSEOUT.md#current-phase-4-exit-condition-disposition) |
| Supported schema/version window agreed and tested | Evidenced | [Final disposition](history/phase-closeouts/PHASE4_CLOSEOUT.md#current-phase-4-exit-condition-disposition) |

Under D-P4-008 and D-P4-009, Phase 5 retains visible renderer/style, selection,
GUI-editing and resource evidence. Phase 6 retains complete stage-specific
exact-validation/export signatures and invalidation, transient exact-geometry
regeneration/cleanup, output equivalence, rollback and end-to-end performance.
Phase 5 remains unopened. Exact-family support is still fixture-only; operator
wiring, whole-document migration and production output remain excluded.

## Live risks

<a id="qa-audit-risk-log"></a>

[current/risks.json](current/risks.json) owns treatment, accountable owner,
deadline, required work and objective closure evidence. This table is a
dashboard only.

| ID | Severity | Treatment | Present exposure |
| --- | --- | --- | --- |
| PR-01 | High | Remove | Release-critical workflow coverage remains incomplete. |
| PR-02 | High | Remove | The B15 chair body could be mistaken for final production geometry. |
| PR-03 | High | Mitigate | Scan/CAD evidence could be mistaken for canonical geometry. |
| PR-04 | High | Mitigate | Scans cannot establish nominal, hidden or rail-fit geometry alone. |
| PR-05 | Medium | Remove | Chair assimilation could add unsuitable runtime dependencies. |
| PR-06 | High | Remove | Imported chair evidence may have unresolved rights. |
| PR-07 | High | Mitigate | Software licensing could be conflated with output licensing. |
| PR-08 | High | Remove | Copied tables could be relabelled as isolated facts. |
| PR-09 | Critical | Remove | A restricted dependency could reach an advertised production path. |
| PR-10 | High | Remove | Duplicate definitions or patches could hide the live implementation. |
| PR-11 | Medium | Tolerate | Modularisation may add files without reducing runtime cost. |
| PR-12 | Medium | Mitigate | Governance can duplicate facts and grow stale. |
| PR-13 | Critical | Mitigate | Commands, history changes or disk failure could destroy unprotected data. |
| PR-14 | High | Remove | Lightweight editing could lose required FreeCAD GUI behaviour. |
| PR-15 | High | Mitigate | Deferred geometry could move rather than remove operator cost. |
| PR-16 | High | Mitigate | Incomplete signatures could reuse stale results. |
| PR-17 | Critical | Mitigate | Persistence or migration could corrupt supported documents. |
| PR-18 | High | Remove | Legacy/modular dual paths could become permanent duplication. |
| PR-19 | High | Remove | A distributed Addon could drift from authoritative source. |
| PR-20 | Medium | Mitigate | Feature work could silently expand migration scope. |
| PR-21 | High | Mitigate | Source provenance or licence could become ambiguous. |
| PR-22 | High | Remove | A true authority transfer could occur without structured challenge. |
| QA-R03 | High | Remove | Release-critical GUI and end-to-end evidence remains incomplete. |
| QA-R04 | High | Mitigate | Modular end-to-end performance budgets remain unfrozen. |
| QA-R05 | Low | Tolerate | Root navigation exists; install and operator guidance remains future work. |

## Owner decisions

[history/phase-closeouts/PHASE4_GATE_DECISIONS.json](history/phase-closeouts/PHASE4_GATE_DECISIONS.json)
owns the displayed Phase 4 decisions; detailed evidence is in the frozen
closeout. [current/gate-decisions.json](current/gate-decisions.json) is clean
for unopened Phase 5.

| ID | Date | Status | Decision boundary |
| --- | --- | --- | --- |
| D-P4-001 | 2026-07-22 | Accepted | Phase 4 opened. |
| D-P4-002 | 2026-07-22 | Accepted | Transition-state v1, chair-package v1 and bounded B14/B15 read-only ingress accepted. |
| D-P4-003 | 2026-07-27 | Accepted | Product comparison route retired while the development oracle and rollback evidence remain. |
| D-P4-004 | 2026-07-27 | Accepted | Independent PR-17 recommendation accepted with bounded conditions. |
| D-P4-005 | 2026-07-27 | Accepted | Exact fixture-only family support accepted; operator wiring and production output excluded. |
| D-P4-006 | 2026-07-27 | Accepted | Product implementation paused until the owner resumes it. |
| D-GOV-001 | 2026-07-27 | Accepted | Governance simplification, fixed current paths, narrowed panels, governance budget and CI adopted. |
| D-GOV-002 | 2026-07-27 | Accepted | Three task levels adopted: routine, behavioural, and authority or release. |
| D-GOV-003 | 2026-07-28 | Accepted | Strict app-bound validation required on protected `main`; QA-R02 closed. |
| D-P4-007 | 2026-07-28 | Accepted | Product implementation resumed for the bounded derived-state lifecycle tranche only. |
| D-P4-008 | 2026-07-28 | Accepted | Cross-phase renderer and exact/export duties assigned to Phases 5 and 6; revised Phase 4 scope is 6/6 evidenced but not closed. |
| D-P4-009 | 2026-07-28 | Accepted | Phase 4 closed at 6/6; evidence and Phase 4 registers frozen; Phase 5 remains not started. |

## Authority and evidence links

- [Current unopened Phase 5 record](current/PHASE_EVIDENCE.md)
- [Frozen Phase 4 closeout](history/phase-closeouts/PHASE4_CLOSEOUT.md)
- [Frozen Phase 4 decisions](history/phase-closeouts/PHASE4_GATE_DECISIONS.json)
- [Frozen Phase 4 risk snapshot](history/phase-closeouts/PHASE4_RISKS.json)
- [Engineering policy](ENGINEERING_POLICY.md)
- [Architecture](ARCHITECTURE.md)
- [Modularisation boundaries](MODULARISATION_PLAN.md)
- [Validation strategy](VALIDATION.md)
- [Recovery and backup](RECOVERY_AND_BACKUP.md)
- [Licensing boundaries](LICENSING_BOUNDARIES.md)
- [Provenance](PROVENANCE.md)
- [Frozen evidence policy and manifest](history/README.md)
