# Project Plan

Status: **Phase 6 current — 2/5 accepted exits. The owner accepted Exit 2 under D-P6-002 on 2026-08-02 and Exit 3 under D-P6-005 on 2026-08-15. Exits 1, 4, and 5 stay Pending.**

This dashboard owns phase and exit status. It also owns live-risk summaries, owner-decision summaries, and evidence links. The canonical status, evidence, and registers are the source of the owner view. The owner view does not establish authority.

The active program is the TrackTemplate Core macro-to-Addon migration in [PRODUCT_VISION.md](PRODUCT_VISION.md). The migration has defined completion conditions. The Addon must be the usual route. The modular package must be the sole runtime without a legacy-macro dependency. The owner must accept the Core parity and output that the project claims. Each distribution build must give the same result. Release qualification must pass.

The Layout Editor is the later program. It does not change Phase 6 exits. The project can record future architecture without current implementation.

## Current owner view

| Field | Current position |
| --- | --- |
| **Current state** | Phase 6 has 2/5 accepted exits. The owner accepted Exits 2 and 3. Exits 1, 4, and 5 stay Pending. Output is private-development. Project status stays `unknown`. |
| **What changed** | [D-GOV-011](current/PHASE_EVIDENCE.md#phase-6-exit-4-d-gov-011-direction-selection-panel) selects one subsequent hypothesis for the measured canonical area of Edit. It bounds the product change at Level 2 to one FreeCAD adapter file. D-GOV-009, D-GOV-010, and their evidence do not change. |
| **What now works** | The same-host attribution result in D-GOV-009 and the source assessment connect the measured canonical area to two repeated reads of the selected record. A subsequent product change can remove those reads without work in a different Edit stage. |
| **Limitations/findings** | The attribution noise floor is `2.895891 ms`. The first quartile of the canonical area was only `0.0731425 ms` higher than that floor. The evidence does not report the cost of each operation in that area. The selected hypothesis can fail its subsequent comparison. No result is improvement evidence or Exit 4 evidence. |
| **Owner decision** | Accept D-GOV-011. Authorise one subsequent product change at Level 2 in `tracktemplate/adapters/freecad/transition_state.py`. Keep one live read of the selected record before the write. Keep the necessary read after the write. Preserve all specified invariants. |
| **Next action** | In a new cycle, make the D-GOV-011 change at Level 2. First, record a new same-host baseline on the D-GOV-010 host. The attribution materiality rule in D-GOV-009 must give a PASS result for the canonical area. If it does not, stop before product work. Do not change the comparison rule. Do not accept Exit 4 without a subsequent owner decision at Level 3. |

## Phase status

| Phase | Outcome | Exit status | State |
| ---: | --- | --- | --- |
| 0 | Recoverable baseline and benchmark checkpoint | 6/6 evidenced | Complete — accepted 2026-07-19 |
| 1 | Product, dependency, correctness and performance inventory | 9/9 evidenced | Complete — accepted 2026-07-22 |
| 2 | Minimal modular foundation and validation harness | 5/5 evidenced | Complete — accepted 2026-07-22 |
| 3 | First parity-proven vertical slice | 5/5 evidenced | Complete — accepted 2026-07-22 |
| 4 | Canonical state, signatures and persistence | 6/6 evidenced | Complete — accepted 2026-07-28 |
| 5 | Lightweight editing prototype and renderer decision | 4/4 evidenced | Complete — accepted 2026-08-01 |
| 6 | Explicit exact-validation and export seam | 2/5 accepted exits | Current — opened 2026-08-01 |
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
| Export is deterministic and failure-safe | Evidenced — owner-accepted 2026-08-15 | [D-P6-005 evidence-admission decision](current/PHASE_EVIDENCE.md#phase-6-exit-3-supported-model-evidence-admission-panel) |
| Editing resource use improves beyond normal noise, with complete end-to-end cost accounted for | Pending | [Current disposition](current/PHASE_EVIDENCE.md#current-phase-6-exit-condition-disposition) |
| The legacy path remains available until parity and project-owner acceptance permit removal | Pending | [Current disposition](current/PHASE_EVIDENCE.md#current-phase-6-exit-condition-disposition) |

D-P5-002 accepted Coin and the demonstrated B16 Entry/Exit editing boundary,
evidencing all four exact exits; D-P5-003 closed Phase 5 without opening Phase 6.
D-P6-001 later opened Phase 6 at 0/5 for bounded exact-validation and private-development export-seam work.
D-P6-002 accepts only the bounded transient-object Exit 2 and advances Phase 6 to 1/5.
D-P6-003 selects strict add-only, journal-free monotonic completion and authorises its later bounded Level 2 implementation; D-P6-004 defines the finite supported exporter fault model, evidence boundary and restart procedure.
D-P6-005 accepts only the bounded private-development B16 Entry/Exit deterministic, failure-safe DXF-and-manifest route under D-P6-003 and D-P6-004 and advances Phase 6 to 2/5. Production clearance, output equivalence, GUI/operator acceptance, wider exporter-family authority, persistence, retained geometry, legacy retirement, performance, packaging and release authority remain excluded; project status remains `unknown`.

D-GOV-006 qualifies only the exact Linux x86_64 stable Flatpak FreeCAD 1.1.3 profile. The decision keeps the exact 1.1.1 profile and its evidence. It does not qualify FreeCAD 1.1.2 or any other host. No phase, risk, product, output, packaging, or release state changes.

D-GOV-007 authorises only the exact 1.1.1 and 1.1.3 host profiles to supply candidate evidence for Phase 6 performance. A later decision can admit a result only if it comes from one of those profiles. D-GOV-007 admits no performance result and defines no budget. It accepts no phase exit and does not claim that performance became better.

D-GOV-008 accepts the PR #50 FreeCAD 1.1.3 series as the comparison baseline. It selects one performance hypothesis for the preview sampler and defines the comparison rule. It authorises one performance optimisation at Level 2 but makes no product change. Exit 4 stays Pending.

D-GOV-009 keeps D-GOV-008 Accepted as the authority for that first direction. It records two subsequent results from Level 2 as retained negative evidence and stops new product work in that direction. It authorised the bounded baseline-attribution investigation at Level 1. The project completed that investigation. The attribution result is direction-selection evidence only. Exit 4 stays Pending.

D-GOV-010 qualifies only the exact FreeCAD 1.1.3 profile with CPython 3.13.13 and PySide6/Qt 6.11.1. It keeps the previously qualified profiles and their evidence. It authorises this profile to supply candidate evidence for performance in a subsequent cycle. Each comparison must use one profile with an exact identity. It admits no performance result and does not change D-GOV-009. Exit 4 stays Pending.

D-GOV-011 selects one subsequent hypothesis for the read route in the canonical FreeCAD adapter. It authorises a product change at Level 2 that can remove only two repeated reads of the selected record. The change must use the exact host in D-GOV-010. It must record a new same-host baseline and must not change the comparison rule. D-GOV-011 makes no product change and admits no performance result. Exit 4 stays Pending.

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

[history/phase-closeouts/PHASE4_GATE_DECISIONS.json](history/phase-closeouts/PHASE4_GATE_DECISIONS.json) owns the displayed Phase 4 decisions.
[history/phase-closeouts/PHASE5_GATE_DECISIONS.json](history/phase-closeouts/PHASE5_GATE_DECISIONS.json) owns the displayed Phase 5 decisions.
The [current decision register](current/gate-decisions.json) owns Phase 6 and current cross-phase governance decisions.

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
| D-P6-004 | 2026-08-15 | Accepted | Supported exporter fault model, interruption-evidence boundary and restart containment accepted without changing product source, risk disposition, Phase 6 at 1/5 or Exit 3 Pending. |
| D-P6-005 | 2026-08-15 | Accepted | Phase 6 Exit 3 accepted only for the bounded private-development B16 Entry/Exit deterministic DXF-and-manifest route under D-P6-003 and D-P6-004; Phase 6 advances to 2/5 and all stated limitations and exclusions remain. |
| TT-DOC-001 | 2026-08-15 | Accepted | Human comprehensibility is a governance control. ASD-STE100 Issue 9 is the normative standard for canonical technical prose in English. No phase, risk, or product authority changes. |
| TT-DOC-002 | 2026-08-15 | Accepted | ASD-STE100 Issue 9 stays the normative standard. TrackTemplate uses UK English spelling as its project spelling directive. No other TT-DOC-001 or project authority changes. |
| D-GOV-006 | 2026-08-15 | Accepted | The project owner qualified the exact Linux x86_64 stable Flatpak FreeCAD 1.1.3 profile. No product, phase, risk, output, packaging, or release state changed. |
| D-GOV-007 | 2026-08-16 | Accepted | The project owner authorised the exact 1.1.1 and 1.1.3 host profiles to supply Phase 6 performance evidence. Exit 4 stays Pending. |
| D-GOV-008 | 2026-08-16 | Accepted | The owner accepted the PR #50 baseline, selected the performance hypothesis for zero-origin integration, and defined the comparison rule. Exit 4 stays Pending. |
| D-GOV-009 | 2026-08-23 | Accepted | The owner records the D-GOV-008 direction as exhausted for new product work. The decision preserves the two negative results and selects a bounded Level 1 baseline-attribution investigation as the next action. Exit 4 stays Pending. |
| D-GOV-010 | 2026-08-23 | Accepted | The owner qualifies only the exact FreeCAD 1.1.3 profile with CPython 3.13.13 and PySide6/Qt 6.11.1. Previous profiles stay qualified. Exit 4 stays Pending. |
| D-GOV-011 | 2026-08-23 | Accepted | The owner selects one subsequent hypothesis for the read route in the canonical FreeCAD adapter. The decision defines the exact host, product boundary, preserved invariants, and comparison rule. Exit 4 stays Pending. |

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
- [Engineering policy and TT-DOC-001 profile](ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile) and [Architecture](ARCHITECTURE.md)
- [Modularisation boundaries](MODULARISATION_PLAN.md)
- [Validation strategy](VALIDATION.md)
- [Runtime and legacy ingress compatibility contract](contracts/phase1-compatibility.json)
- [Recovery and backup](RECOVERY_AND_BACKUP.md)
- [Licensing boundaries](LICENSING_BOUNDARIES.md)
- [Provenance](PROVENANCE.md)
- [Frozen evidence policy and manifest](history/README.md)
