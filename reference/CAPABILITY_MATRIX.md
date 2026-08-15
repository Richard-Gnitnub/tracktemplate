# TrackTemplate Capability Matrix

Status: **Current repository-evidence map for the product plan. It gives no
phase, migration-family, output-clearance, or release acceptance.**

This matrix compares the accepted legacy baseline with the modular B16
checkpoint for the Addon. The TT-DOC-001 panel reconciled it on 2026-08-15.
The panel used protected `main` at
`f03818d71bce06c5cfb85da84d8f3f230e08b47c`. It also used the frozen Phase 1
inventory, Phase 5 closeout, and current Phase 6 evidence. D-P6-002 accepts the
bounded transient-object exit. D-P6-005 accepts only the bounded
private-development exporter failure-safety claim. Neither decision grants
output clearance.

The Addon column describes the modular `tracktemplate` implementation, not an
installable or production-ready Addon claim. [PROJECT_PLAN.md](PROJECT_PLAN.md)
owns formal phase status.

## Status vocabulary

- **C — current:** present and evidenced for the stated bounded scope.
- **P — partial:** some implementation or evidence exists, but the named
  capability is incomplete or narrower than the product capability.
- **A — absent:** no implementation for that capability exists on the audited
  accepted modular source.
- **F — future:** belongs to the subsequent Layout Editor programme.
- **U — unknown:** the inspected repository evidence does not settle the cell.
- **—:** not applicable to that capability.

The final classification is a planning summary, not acceptance. A row may be
`Partial` because a strong legacy oracle exists while the Addon implementation
is absent.

## Matrix

| Capability | Legacy macro baseline | Current Addon | Canonical state | Coin presentation | Exact geometry | Export | Persistence | Accepted fixture or evidence | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Straight track | C — bounded straight/station workflow | A | A | A | A | A | A | [Phase 1 workflow inventory](phase-evidence/PHASE1_INVENTORY.md#release-critical-workflow-coverage-inventory); [straight/station series](benchmarks/2026-07-20-b14-straight-station-workflow-series.md) | Partial |
| Curves | C — bounded curve/easement create, edit and output oracles | P — Entry/Exit transition slice only | P — transition-state v1 only | P — transition centreline only | P — transition centreline only | P — private-development DXF only | P — transition records only | [Phase 1 workflow contract](contracts/phase1-workflow-coverage.json); [Phase 5 closeout](history/phase-closeouts/PHASE5_CLOSEOUT.md); [Phase 6 evidence](current/PHASE_EVIDENCE.md) | Partial |
| Euler transitions | C — accepted B14/B15 calculation and workflow evidence | C — bounded B16 Entry/Exit slice | C — signed transition-state v1 boundary | C — accepted bounded centreline view | C — transient exact centreline | P — private-development DXF only | C — bounded transition records | [Transition pilot](contracts/phase1-transition-pilot.json); [Phase 5 closeout](history/phase-closeouts/PHASE5_CLOSEOUT.md); [Phase 6 evidence](current/PHASE_EVIDENCE.md) | Partial |
| Multiple parallel tracks | C — fixed two-track fixture | P — fixture-only Entry/Exit records for one secondary track | P | P — representative pair only | P — transition records only | A | P | [Workflow coverage contract](contracts/phase1-workflow-coverage.json); [Phase 5 closeout](history/phase-closeouts/PHASE5_CLOSEOUT.md#representative-multi-object-selection-and-edit-tranche) | Partial |
| General track widening | P — B14 source contains a general track/platform-widening route; no dedicated accepted general-widening fixture was found | A — spacing-transition evidence does not establish general widening | A for general widening | A for general widening | A for general widening | A | A for general widening | [B14 oracle](../AdvancedTurnout.FCMacro); [Phase 1 workflow inventory](phase-evidence/PHASE1_INVENTORY.md#release-critical-workflow-coverage-inventory) | Partial |
| Spacing-matched Entry/Exit transitions | C — accepted spacing-matched secondary plain-line Entry/Exit fixture | P — fixture-only accepted Entry/Exit slice | P — transition-state v1 records derived from start/curve/finish spacing | P — bounded transition centreline pair only | P — transient transition centrelines only | P — private-development DXF only | P — bounded transition records only | [Phase 4 closeout](history/phase-closeouts/PHASE4_CLOSEOUT.md#exact-family-support-enablement); [Phase 5 closeout](history/phase-closeouts/PHASE5_CLOSEOUT.md#representative-multi-object-selection-and-edit-tranche); [Phase 6 evidence](current/PHASE_EVIDENCE.md#phase-6-exits-2-and-3-evidence-admission-panel) | Partial |
| Turnouts | C — bounded REA C10 lifecycle oracle | A | A | A | A | A | A | [Workflow coverage contract](contracts/phase1-workflow-coverage.json); [turnout series](benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md) | Partial |
| Crossovers | C — bounded XO-001 geometry and lifecycle evidence | A | A | A | A | A | A | [Crossover feasibility contract](contracts/phase1-crossover-feasibility.json); [workflow coverage contract](contracts/phase1-workflow-coverage.json) | Partial |
| Sleepers and turnout timbers | C — bounded automatic crossover-timbering evidence | A | A | A | A | A | A | [Timbering contract](contracts/phase1-crossover-timbering.json); [Phase 1 workflow inventory](phase-evidence/PHASE1_INVENTORY.md#release-critical-workflow-coverage-inventory) | Partial |
| Chair analysis | C — bounded logical analysis, invalidation and persistence evidence | A — chair analysis is not migrated | A | A | A | A | A | [Chair persistence contract](contracts/phase1-chair-analysis-persistence.json); [chair invalidation contract](contracts/phase1-chair-analysis-invalidation.json) | Partial |
| Procedural chairs and support components | P — five-box bodies are legacy gap evidence, not the production oracle | P — neutral package validation boundary only | P — chair-definition package v1 | A | A | A | P — serialisable package, not supported FreeCAD product persistence | [Chair package fixture](../tests/fixtures/chair-definition-v1-contract.json); [architecture boundary](ARCHITECTURE.md#chair-definition-and-procedural-geometry-contract) | Partial |
| Platforms | P — substantial B14 source exists; the accepted inventory retains physical platform and wider-workflow gaps | A | A | A | A | A | A | [B14 oracle](../AdvancedTurnout.FCMacro); [Phase 1 workflow inventory](phase-evidence/PHASE1_INVENTORY.md#release-critical-workflow-coverage-inventory) | Partial |
| Formation boards | P — substantial B14 source exists; no dedicated accepted formation-board migration fixture was found | A | A | A | A | A | A | [B14 oracle](../AdvancedTurnout.FCMacro); [Phase 1 inventory](phase-evidence/PHASE1_INVENTORY.md) | Partial |
| SVG | C — fixed plain-line selected and Generate-path output oracles | A | P — bounded transition intent exists, not an SVG output contract | — | P — centreline-only exact seam | A | — | [Workflow coverage contract](contracts/phase1-workflow-coverage.json); [selected-export series](benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md) | Partial |
| DXF | C — fixed plain-line selected and Generate-path output oracles | P — private-development Entry/Exit writer only | P — bounded transition intent exists | — | P — transient transition centreline | P — deterministic output and supported-model failure safety owner-accepted under D-P6-005 for the bounded private-development Entry/Exit route only | — | [Workflow coverage contract](contracts/phase1-workflow-coverage.json) and [current Phase 6 evidence](current/PHASE_EVIDENCE.md#phase-6-exit-3-supported-model-evidence-admission-panel) | Partial |
| STL | C — fixed plain-line legacy output oracle | A | A for solids/meshes | — | A for required production solids/meshes | A | — | [Workflow coverage contract](contracts/phase1-workflow-coverage.json); [create-time export series](benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md) | Partial |
| STEP | C — fixed plain-line legacy output oracle | A | A for B-rep production scope | — | A for required production B-reps | A | — | [Workflow coverage contract](contracts/phase1-workflow-coverage.json); [create-time export series](benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md) | Partial |
| Calibrated map or image reference layers | U | F | F | F | — | U | F | [Product vision](PRODUCT_VISION.md#subsequent-programme-tracktemplate-layout-editor); no accepted implementation fixture found | Future |
| FreeCAD sketch reference layers | U | F | F | F | — | U | F | [Product vision](PRODUCT_VISION.md#subsequent-programme-tracktemplate-layout-editor); no accepted implementation fixture found | Future |
| Complete-template placement and rotation | U for the Layout Editor meaning | F | F | F | — | U | F | [Product vision](PRODUCT_VISION.md#subsequent-programme-tracktemplate-layout-editor); existing turnout host placement is a different bounded legacy workflow | Future |
| Connected placement, extension, attach and detach | U for the Layout Editor meaning | F | F | F | — | U | F | [Product vision](PRODUCT_VISION.md#subsequent-programme-tracktemplate-layout-editor); no accepted connected-layout fixture found | Future |
| Constituent template geometry editing | U | F | F | F | F where later validation requires it | U | F | [Product vision](PRODUCT_VISION.md#subsequent-programme-tracktemplate-layout-editor); no accepted implementation fixture found | Future |
| Fixed-end fitting and connected-layout solving | U | F | F | F | F where later validation requires it | U | F | [Product vision](PRODUCT_VISION.md#subsequent-programme-tracktemplate-layout-editor); no accepted solver fixture found | Future |

## Evidence limits and maintenance

`C` never widens the evidence named in its cell. In particular, the accepted
Coin and transient exact-geometry results cover the B16 Entry/Exit transition
slice, not a shared renderer, complete curve family or whole layout. A legacy
`C` does not mean that the capability has migrated.

The spacing-matched Entry/Exit row is confined to the accepted bounded
centreline, transition-record and private-development DXF slice. It does not
establish general track widening, a shared renderer, complete rail,
sleeper/timber or chair presentation, manufacturing geometry, output
equivalence, production clearance or any Phase 6 exit beyond D-P6-002's
bounded transient-object acceptance.

Update this matrix only from accepted repository evidence. Use `U` when a
source search or general product description cannot establish a tested
capability. Keep phase/exit changes in [PROJECT_PLAN.md](PROJECT_PLAN.md),
tranche evidence in [current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md), and
future programme scope in [PRODUCT_VISION.md](PRODUCT_VISION.md).
