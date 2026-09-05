# Project Plan

Status: **Phase 7 is Open at 0/4 under D-P7-001 on 2026-09-05. Phase 6 is closed with four accepted exits and one deferred, unmet obligation. D-P6-008 stays in full.**

This dashboard owns phase and exit status. It also owns summaries of live risks and owner decisions. The links identify the applicable evidence. The canonical registers and evidence are the source of this owner view. This view does not establish authority.

The active programme is the TrackTemplate Core macro-to-Addon migration in [PRODUCT_VISION.md](PRODUCT_VISION.md). The migration has defined completion conditions. The Addon must be the usual route. The modular `tracktemplate` package must contain the one authoritative product implementation. The Addon must not use the legacy macro when the product operates. The owner must accept the claimed Core parity and output. Each distribution build must give the same result. Release qualification must pass.

The Layout Editor is the later programme. It does not change the Phase 6 exits. The project can record its future architecture without current implementation.

## Current owner view

| Field | Current position |
| --- | --- |
| **Current state** | Phase 7 is Open at 0/4. All four exits are Pending. Phase 6 is closed with four accepted exits and one deferred, unmet obligation. The output has private-development status. Project status stays `unknown`. |
| **What changed** | [D-P7-001](current/PHASE_EVIDENCE.md#phase-7-opening-panel) opens the existing Core alignment, station and multiple-track migration scope. The owner authorises opening integration and the first bounded product task. |
| **What now works** | The opening records define the authorised sequence and first task. This alignment changes no product source. |
| **Limitations/findings** | The owner accepts no performance result. PR-15 and QA-R04 stay High/Mitigate/Partial. All legacy-retirement conditions and wider exclusions still apply. D-GOV-011 stays stopped with its retained negative evidence. |
| **Owner decision** | Richard opened Phase 7 at 0/4. He authorised integration of the exact-green opening alignment, then the bounded product task through validation, independent review and publication. |
| **Next action** | Integrate the opening alignment and synchronise clean protected main. Then move `main_circle_centre` into the modular package and route the existing B16 Generate/Replace caller through it. The later product pull request needs separate owner integration authority. |

## Phase status

| Phase | Outcome | Exit status | State |
| ---: | --- | --- | --- |
| 0 | Recoverable baseline and performance-comparison checkpoint | 6/6 evidenced | Complete — accepted 2026-07-19 |
| 1 | Product, dependency, correctness and performance inventory | 9/9 evidenced | Complete — accepted 2026-07-22 |
| 2 | Minimal modular foundation and validation harness | 5/5 evidenced | Complete — accepted 2026-07-22 |
| 3 | First parity-proven vertical slice | 5/5 evidenced | Complete — accepted 2026-07-22 |
| 4 | Canonical state, signatures, and persistence | 6/6 evidenced | Complete — accepted 2026-07-28 |
| 5 | Lightweight editing prototype and renderer decision | 4/4 evidenced | Complete — accepted 2026-08-01 |
| 6 | Explicit exact-validation and export seam | 4/5 accepted exits; one deferred, unmet obligation | Complete — accepted 2026-09-05 |
| 7 | Core alignment, station and multiple-track migration | 0/4 evidenced | Open |
| 8 | Turnout, crossover and timbering migration | 0/4 evidenced | Not started |
| 9 | Chair definitions, assisted assimilation, production records and export completion | 0/9 evidenced | Not started |
| 10 | Workbench integration, launcher reduction and beta Addon packaging | 0/5 evidenced | Not started |
| 11 | Stabilisation and qualification of the version proposed for release | 0/7 evidenced | Not started |

## Phase 6 exit conditions

| Exit condition | Status | Evidence |
| --- | --- | --- |
| The selected slice has equivalent exact validation and production output for the agreed bounded scope | Evidenced — owner-accepted 2026-09-05 | [D-P6-006 panel and decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-1-bounded-output-evidence-admission-panel) |
| No transient production objects leak into the editable document | Evidenced — owner-accepted 2026-08-02 | [D-P6-002 panel and decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exits-2-and-3-evidence-admission-panel) |
| The same export input gives the same output, and export is failure-safe | Evidenced — owner-accepted 2026-08-15 | [D-P6-005 decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-3-supported-model-evidence-admission-panel) |
| Editing resource use improves beyond normal noise, with complete end-to-end cost accounted for | Deferred — unmet | [D-P6-008 panel and decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-4-deferral-panel) |
| The legacy path remains available until parity and project-owner acceptance permit removal | Evidenced — owner-accepted 2026-09-05 | [D-P6-007 panel and decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-5-preservation-evidence-admission-panel) |

D-P6-009 closes Phase 6 without opening Phase 7. The owner accepted the completed independent recovery proof. The accepted Phase 6 decisions, bounded output limits, stopped directions, and negative evidence remain in the frozen closeout. All risks and legacy-retirement conditions still apply. Project status stays `unknown` and output stays private-development.

D-P6-008 stays in full, and normal per-slice checks stay mandatory. The unchanged improvement obligation for the bounded Entry/Exit scope is mandatory before Phase 10 beta acceptance. Richard keeps accountability and owns delivery until a named Phase 10 integration owner takes delivery responsibility. Independent review and Richard's acceptance are mandatory. Numerical budgets or improvement on another workload do not give the required evidence for this obligation. If it stays unmet, Richard must not accept beta.

## Phase 7 exit conditions

Phase 7 is Open at 0/4 under D-P7-001. These four original criteria from accepted plan revision `d5a3db45ab68a192e3d37f9fad5deb9f66f7de81` stay unchanged. The first task does not narrow the phase.

| Exit condition | Status | Evidence |
| --- | --- | --- |
| Core layouts can be created, edited, saved, reopened, validated, and exported through modular paths. | Pending | No Phase 7 admission |
| Accepted B14/B15 geometry, station mapping, identities, ordering, and metadata remain equivalent. | Pending | No Phase 7 admission |
| Domain calculations for this family have no FreeCAD/Qt dependency or reverse adapter import. | Pending | No Phase 7 admission |
| Legacy core-layout paths have either been safely retired or have a documented blocker and removal gate. | Pending | No Phase 7 admission |

## Live risks
<a id="qa-audit-risk-log"></a>

[current/risks.json](current/risks.json) owns treatment, accountable owner, deadline, required work and objective closure evidence. This table is a dashboard only.

| ID | Severity | Treatment | Present exposure |
| --- | --- | --- | --- |
| PR-01 | High | Remove | Release-critical workflow coverage remains incomplete. |
| PR-02 | High | Remove | The B15 chair body could be mistaken for final production geometry. |
| PR-03 | High | Mitigate | Scan/CAD evidence could be mistaken for canonical geometry. |
| PR-04 | High | Mitigate | Scans cannot establish nominal, hidden or rail-fit geometry alone. |
| PR-05 | Medium | Remove | Chair assimilation could add unsuitable product runtime dependencies. |
| PR-06 | High | Remove | Imported chair evidence may have unresolved rights. |
| PR-07 | High | Mitigate | Software licensing could be conflated with output licensing. |
| PR-08 | High | Remove | Copied tables could be relabelled as isolated facts. |
| PR-09 | Critical | Remove | A restricted dependency could reach an advertised production path. |
| PR-10 | High | Remove | Duplicate definitions or patches could hide the live implementation. |
| PR-11 | Medium | Tolerate | Modularisation may add files without reducing cost when the software operates. |
| PR-12 | Medium | Mitigate | Product direction or task selection can fragment and grow stale. |
| PR-13 | Critical | Mitigate | Commands, history changes or disk failure could destroy unprotected data. |
| PR-15 | High | Mitigate | Deferred geometry could move rather than remove operator-journey cost. |
| PR-16 | High | Mitigate | Incomplete signatures could reuse stale results. |
| PR-17 | Critical | Mitigate | Persistence or migration could corrupt supported documents. |
| PR-18 | High | Remove | Legacy/modular dual paths could become permanent duplication. |
| PR-19 | High | Remove | A distributed Addon could drift from authoritative source. |
| PR-20 | Medium | Mitigate | Future-product direction could silently expand the migration bounded scope or leak derived authority. |
| PR-21 | High | Mitigate | Source provenance or licence could become ambiguous. |
| PR-22 | High | Remove | Authority could transfer, or self-acceptance occur, without independent challenge. |
| QA-R03 | High | Remove | Release-critical GUI and end-to-end evidence remains incomplete. |
| QA-R04 | High | Mitigate | Modular end-to-end performance budgets remain unfrozen. |
| QA-R05 | Low | Tolerate | Root navigation exists. Installation and person guidance remain future work. |

## Owner decisions

The frozen [Phase 4](history/phase-closeouts/PHASE4_GATE_DECISIONS.json), [Phase 5](history/phase-closeouts/PHASE5_GATE_DECISIONS.json), and [Phase 6](history/phase-closeouts/PHASE6_GATE_DECISIONS.json) registers own their historical decisions below. The [current decision register](current/gate-decisions.json) keeps D-P6-008 in full and records D-P7-001.

| ID | Date | Status | Decision limit |
| --- | --- | --- | --- |
| D-P4-001 | 2026-07-22 | Accepted | Phase 4 opened. |
| D-P4-002 | 2026-07-22 | Accepted | Transition-state v1, chair-package v1 and bounded B14/B15 read-only ingress accepted. |
| D-P4-003 | 2026-07-27 | Accepted | The product comparison route retired. The development oracle and rollback evidence remain. |
| D-P4-004 | 2026-07-27 | Accepted | Independent PR-17 recommendation accepted with bounded conditions. |
| D-P4-005 | 2026-07-27 | Accepted | Exact fixture-only family support accepted. Wiring for the person who operates the product and production output are excluded. |
| D-P4-006 | 2026-07-27 | Accepted | Product implementation paused until the owner resumes it. |
| D-GOV-001 | 2026-07-27 | Accepted | Governance simplification, fixed current paths, narrowed panels, governance budget and CI adopted. |
| D-GOV-002 | 2026-07-27 | Accepted | Three task levels adopted: routine, behavioural, and authority or release. |
| D-GOV-003 | 2026-07-28 | Accepted | Strict app-bound validation is required on protected `main`. QA-R02 closed. |
| D-P4-007 | 2026-07-28 | Accepted | Product implementation resumed only for the bounded derived-state lifecycle cycle. |
| D-P4-008 | 2026-07-28 | Accepted | Phases 5 and 6 received the renderer and exact-export duties. The revised Phase 4 bounded scope is 6/6 evidenced but not closed. |
| D-P4-009 | 2026-07-28 | Accepted | Phase 4 closed at 6/6. Its evidence and registers are frozen. Phase 5 remains not started. |
| D-P5-001 | 2026-07-28 | Accepted | Phase 5 opened at 0/4 for bounded lightweight-renderer evaluation. No renderer was accepted. |
| D-GOV-004 | 2026-07-31 | Accepted | A literal `$tracktemplate-continue` invocation can run one bounded repository-driven Level 1 or Level 2 cycle. Level 3 authority remains excluded. The cycle gives no merge authority for a new draft created in that cycle. |
| D-P5-002 | 2026-07-31 | Accepted | Coin and the demonstrated B16 Entry/Exit editing behaviour accepted. All 4/4 exits are evidenced. Closeout remained a separate decision. |
| D-P5-003 | 2026-08-01 | Accepted | Phase 5 closed at 4/4. Phase 6 holding records were created at 0/5 without opening or authorising the phase. |
| D-P6-001 | 2026-08-01 | Accepted | Phase 6 opened at 0/5. It authorised bounded B16 Entry/Exit exact validation and private-development export-seam work. All stated exclusions remain. |
| D-GOV-005 | 2026-08-01 | Accepted | The decision adopted the Product Vision, architecture direction, and Product-Vision work selection. It did not change the Phase 6 bounded scope or D-GOV-004 authority. |
| D-P6-002 | 2026-08-02 | Accepted | Only Phase 6 Exit 2 is evidenced and owner-accepted for the bounded B16 Entry/Exit slice. Exit 3 remains Pending. Phase 6 is 1/5. |
| D-P6-003 | 2026-08-02 | Accepted | The decision selected completion that can only add output members. It keeps no separate journal, and the completion count can only increase. It authorised a later Level 2 implementation. Exit 3 remains Pending. Phase 6 remains 1/5. |
| D-P6-004 | 2026-08-15 | Accepted | The supported exporter fault model, interruption-evidence limit, and restart containment are accepted. Product source, risk disposition, Phase 6 at 1/5, and Exit 3 Pending do not change. |
| D-P6-005 | 2026-08-15 | Accepted | The decision accepts Phase 6 Exit 3 only for the bounded B16 Entry/Exit DXF-and-manifest route. The route has private-development status and uses D-P6-003 and D-P6-004. Phase 6 advances to 2/5. All stated limitations and exclusions remain. |
| D-P6-006 | 2026-09-05 | Accepted | The [decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-1-bounded-output-evidence-admission-panel) accepts Exit 1 for the agreed scope of the PR #63 comparison of Entry/Exit centrelines. Phase 6 advances to 3/5. Exits 4 and 5 stay Pending. All stated limitations and exclusions still apply. |
| D-P6-007 | 2026-09-05 | Accepted | The [decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-5-preservation-evidence-admission-panel) accepts Exit 5 for continued legacy preservation in the bounded Entry/Exit slice. Phase 6 advances to 4/5. Exit 4 stays Pending. All retirement conditions and wider exclusions still apply. The owner authorises no removal. |
| D-P6-008 | 2026-09-05 | Accepted | The [decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#phase-6-exit-4-deferral-panel) gives Exit 4 Deferred — unmet status. Its unchanged obligation stays mandatory before Phase 10 beta acceptance. Phase 6 keeps four accepted exits and one deferred, unmet obligation. The owner accepts only the bounded sequencing exposure. Phase closure and Phase 7 opening need different decisions. |
| D-P6-009 | 2026-09-05 | Accepted | Phase 6 closed with four accepted exits and one deferred, unmet obligation. The owner accepts the completed recovery proof. D-P6-008 stays in full. Phase 7 stays unopened at 0/4. The owner also authorises exact-green closeout integration. |
| D-P7-001 | 2026-09-05 | Accepted | The [decision](current/PHASE_EVIDENCE.md#phase-7-opening-panel) opens Phase 7 at 0/4 with its four criteria unchanged. It authorises opening integration and the bounded `main_circle_centre` product task through publication. D-P6-008 stays in full. No exit or performance result is accepted. |
| TT-DOC-001 | 2026-08-15 | Accepted | Human comprehensibility is a governance control. ASD-STE100 Issue 9 is the normative standard for canonical technical prose in English. No phase, risk, or product authority changes. |
| TT-DOC-002 | 2026-08-15 | Accepted | ASD-STE100 Issue 9 stays the normative standard. TrackTemplate uses UK English word forms in TT-DOC-001 canonical prose. No other TT-DOC-001 or project authority changes. |
| D-GOV-006 | 2026-08-15 | Accepted | The project owner qualified the exact Linux x86_64 stable Flatpak FreeCAD 1.1.3 profile. No product, phase, risk, output, packaging, or release state changed. |
| D-GOV-007 | 2026-08-16 | Accepted | The project owner authorised the exact 1.1.1 and 1.1.3 host profiles to supply Phase 6 performance evidence. Exit 4 stays Pending. |
| D-GOV-008 | 2026-08-16 | Accepted | The owner accepted the PR #50 comparison baseline. The owner selected the performance hypothesis for zero-origin integration and defined the comparison rule. Exit 4 stays Pending. |
| D-GOV-009 | 2026-08-23 | Accepted | The owner records the D-GOV-008 direction as exhausted for new product work. The decision preserves two negative results. It selects a bounded Level 1 baseline-attribution investigation as the next action. Exit 4 stays Pending. |
| D-GOV-010 | 2026-08-23 | Accepted | The owner qualifies only the exact FreeCAD 1.1.3 profile with CPython 3.13.13 and PySide6/Qt 6.11.1. Previous profiles stay qualified. Exit 4 stays Pending. |
| D-GOV-011 | 2026-08-23 | Accepted | The owner selects one later performance hypothesis for the read route in the canonical FreeCAD adapter. The decision defines the exact host, product boundary, preserved invariants, and comparison rule. Exit 4 stays Pending. |
| D-GOV-012 | 2026-08-25 | Accepted | The [decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#d-gov-012-worktree-sequence-nonconformance) records sequence nonconformance after worktree retirement. The owner accepts the preservation audit and its source SHA-256. Cycle 2 authority applies only to an exact candidate. The owner permits a draft pull request but not a merge into protected main. |
| D-GOV-015 | 2026-08-31 | Accepted | The [decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#d-gov-015-simplified-ste-lifecycle) adopts author → freeze scope → one Documentation Review → optional exact reviewed correction once → one final deterministic validation → complete or owner stop. Phase 6 stays at 2/5. If validation is exact-green, the owner permits one draft pull request. The owner gives no merge authority. |
| D-GOV-017 | 2026-09-04 | Accepted | The [decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#d-gov-017-whole-technical-document-lifecycle) establishes one TDMP and the Technical Author Lead responsibility. For governance prose, the finite route is write once under D-GOV-015, one Documentation Review, apply its required adjustment once if any, one final deterministic validation, then done. CI can verify final bytes but cannot reopen review or wording. A general quality review applies only to separately changed source or tests. The stopped additional review returned no result and made no tracked mutation. Phase 6 stays at 2/5, and project status stays `unknown`. |
| D-GOV-018 | 2026-09-05 | Accepted | The [decision](history/phase-closeouts/PHASE6_CLOSEOUT.md#d-gov-018-finite-documentation-completion) authorises one set of exact corrections after the sole review. This includes a `BLOCKED` verdict. Record the `locked` state for the content. Validate it. Finish the cycle. Preserve the initial verdict. Review only complete logical units that changed. Do not expand the repair into unchanged legacy prose. Phase 6 stays at 2/5. |
## Authority and evidence links

- [Current Phase 7 evidence](current/PHASE_EVIDENCE.md)
- [Frozen Phase 6 closeout](history/phase-closeouts/PHASE6_CLOSEOUT.md), [decisions](history/phase-closeouts/PHASE6_GATE_DECISIONS.json), and [risk snapshot](history/phase-closeouts/PHASE6_RISKS.json)
- [Accepted Phase 6 recovery record](backup-records/2026-09-05-phase6-closeout-recovery.md)
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
- [Licensing boundaries](LICENSING_BOUNDARIES.md) and [Provenance](PROVENANCE.md)
- [Frozen evidence policy and manifest](history/README.md)
