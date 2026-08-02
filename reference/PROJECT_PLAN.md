# Project Plan

Status: **Phase 6 current — 1/5 evidenced. Exit 2 was owner-accepted under D-P6-002 on 2026-08-02; exits 1, 3, 4 and 5 remain Pending.**

This file is the project dashboard. It owns only phase status, exit-condition
status, the live-risk summary, owner-decision summary and links to evidence.
Implementation detail belongs in the frozen phase closeout or
[current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md); detailed current risks
and decisions belong in the JSON registers beside the live record.

The active programme is the TrackTemplate Core macro-to-Addon migration in
[PRODUCT_VISION.md](PRODUCT_VISION.md). Migration completes only when the Addon
is the normal route, the modular package is the sole runtime without a legacy-
macro dependency, advertised Core parity/output is accepted, the distribution
is reproducible and release qualification passes. The Layout Editor is
subsequent: it does not alter Phase 6 exits. Future architecture may be recorded
now without being implemented now.

## Phase status

| Phase | Outcome | Exit status | State |
| ---: | --- | --- | --- |
| 0 | Recoverable baseline and benchmark checkpoint | 6/6 evidenced | Complete — accepted 2026-07-19 |
| 1 | Product, dependency, correctness and performance inventory | 9/9 evidenced | Complete — accepted 2026-07-22 |
| 2 | Minimal modular foundation and validation harness | 5/5 evidenced | Complete — accepted 2026-07-22 |
| 3 | First parity-proven vertical slice | 5/5 evidenced | Complete — accepted 2026-07-22 |
| 4 | Canonical state, signatures and persistence | 6/6 evidenced | Complete — accepted 2026-07-28 |
| 5 | Lightweight editing prototype and renderer decision | 4/4 evidenced | Complete — accepted 2026-08-01 |
| 6 | Explicit exact-validation and export seam | 1/5 evidenced | Current — opened 2026-08-01 |
| 7 | Core alignment, station and multiple-track migration | 0/4 evidenced | Not started |
| 8 | Turnout, crossover and timbering migration | 0/4 evidenced | Not started |
| 9 | Chair definitions, assisted assimilation, production records and export completion | 0/9 evidenced | Not started |
| 10 | Workbench integration, launcher reduction and beta Addon packaging | 0/5 evidenced | Not started |
| 11 | Stabilisation and release-candidate qualification | 0/7 evidenced | Not started |

## Phase 6 exit conditions

| Exit condition | Status | Evidence |
| --- | --- | --- |
| The selected slice has equivalent exact validation and production output for the agreed scope | Pending | [Current disposition](current/PHASE_EVIDENCE.md#current-phase-6-exit-condition-disposition) |
| No transient production objects leak into the editable document | Evidenced — owner-accepted 2026-08-02 | [D-P6-002 panel and decision](current/PHASE_EVIDENCE.md#phase-6-exits-2-and-3-evidence-admission-panel) |
| Export is deterministic and failure-safe | Pending | [D-P6-003 contract decision](current/PHASE_EVIDENCE.md#phase-6-exit-3-recovery-authority-contract-panel) |
| Editing resource use improves beyond normal noise, with complete end-to-end cost accounted for | Pending | [Current disposition](current/PHASE_EVIDENCE.md#current-phase-6-exit-condition-disposition) |
| The legacy path remains available until parity and project-owner acceptance permit removal | Pending | [Current disposition](current/PHASE_EVIDENCE.md#current-phase-6-exit-condition-disposition) |

D-P5-002 accepted Coin and the demonstrated B16 Entry/Exit editing boundary,
evidencing all four exact exits; D-P5-003 closed Phase 5 without opening Phase 6.
D-P6-001 later opened Phase 6 at 0/5 for bounded exact-validation and private-development export-seam work.
D-P6-002 accepts only the bounded transient-object Exit 2 and advances Phase 6 to 1/5.
D-P6-003 selects strict add-only, journal-free monotonic completion and authorises its later bounded Level 2 implementation;
Exit 3 remains Pending with condition 1 unimplemented, condition 3 unproved and the fresh condition 6 evidence-admission panel still required. Production clearance,
migration, retained geometry, legacy retirement, performance, packaging and release authority remain excluded.

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
| PR-12 | Medium | Mitigate | Product direction or task selection can fragment and grow stale. |
| PR-13 | Critical | Mitigate | Commands, history changes or disk failure could destroy unprotected data. |
| PR-15 | High | Mitigate | Deferred geometry could move rather than remove operator cost. |
| PR-16 | High | Mitigate | Incomplete signatures could reuse stale results. |
| PR-17 | Critical | Mitigate | Persistence or migration could corrupt supported documents. |
| PR-18 | High | Remove | Legacy/modular dual paths could become permanent duplication. |
| PR-19 | High | Remove | A distributed Addon could drift from authoritative source. |
| PR-20 | Medium | Mitigate | Future-product direction could silently expand migration scope or leak derived authority. |
| PR-21 | High | Mitigate | Source provenance or licence could become ambiguous. |
| PR-22 | High | Remove | Authority could transfer, or self-acceptance occur, without independent challenge. |
| QA-R03 | High | Remove | Release-critical GUI and end-to-end evidence remains incomplete. |
| QA-R04 | High | Mitigate | Modular end-to-end performance budgets remain unfrozen. |
| QA-R05 | Low | Tolerate | Root navigation exists; install and operator guidance remains future work. |

## Owner decisions

[history/phase-closeouts/PHASE4_GATE_DECISIONS.json](history/phase-closeouts/PHASE4_GATE_DECISIONS.json)
owns the displayed Phase 4 decisions, and
[history/phase-closeouts/PHASE5_GATE_DECISIONS.json](history/phase-closeouts/PHASE5_GATE_DECISIONS.json)
owns the displayed Phase 5 decisions. The
[current decision register](current/gate-decisions.json) owns Phase 6
decisions.

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
| D-P5-001 | 2026-07-28 | Accepted | Phase 5 opened at 0/4 for bounded lightweight renderer evaluation; no renderer accepted. |
| D-GOV-004 | 2026-07-31 | Accepted | Literal `$tracktemplate-continue` invocation may run one bounded repository-driven Level 1/2 cycle; all Level 3 and same-cycle new-draft merge authority remains excluded. |
| D-P5-002 | 2026-07-31 | Accepted | Coin and the demonstrated B16 Entry/Exit editing behaviour accepted; 4/4 exits evidenced while closeout remained a separate decision. |
| D-P5-003 | 2026-08-01 | Accepted | Phase 5 closed at 4/4; Phase 6 holding records created at 0/5 without opening or authorising the phase. |
| D-P6-001 | 2026-08-01 | Accepted | Phase 6 opened at 0/5 for bounded B16 Entry/Exit exact-validation and private-development export-seam work; all stated exclusions remain. |
| D-GOV-005 | 2026-08-01 | Accepted | Product vision, architectural direction and vision-led work selection adopted without changing Phase 6 scope or D-GOV-004 execution authority. |
| D-P6-002 | 2026-08-02 | Accepted | Only Phase 6 Exit 2 is evidenced and owner-accepted for the bounded B16 Entry/Exit slice; Exit 3 remains Pending and Phase 6 is 1/5. |
| D-P6-003 | 2026-08-02 | Accepted | Strict add-only, journal-free monotonic completion selected for bounded Exit 3 recovery and a later Level 2 implementation authorised; Exit 3 remains Pending and Phase 6 remains 1/5. |

## Authority and evidence links

- [Current Phase 6 evidence](current/PHASE_EVIDENCE.md)
- [Canonical product vision](PRODUCT_VISION.md)
- [Capability evidence matrix](CAPABILITY_MATRIX.md)
- [Frozen Phase 5 closeout](history/phase-closeouts/PHASE5_CLOSEOUT.md)
- [Frozen Phase 5 decisions](history/phase-closeouts/PHASE5_GATE_DECISIONS.json)
- [Frozen Phase 5 risk snapshot](history/phase-closeouts/PHASE5_RISKS.json)
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
