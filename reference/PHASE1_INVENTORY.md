# Phase 1 Product and Dependency Inventory

Status: **complete and accepted at Phase 1 closeout on 2026-07-22**. This
document owns the Phase 1 inventory and concise decision log. It records the
accepted first extraction slice and initial runtime/legacy-ingress window. The
closeout authorises only the Phase 2 foundation; calculation movement, document
migration and every named later gate remain outside this inventory.

## Purpose

Phase 1 chooses migration order from evidence. The current inventory records a
reproducible static view of the accepted B15 behavioural reference and the B14
legacy oracle, identifies order-sensitive implementation mechanisms, compares
the leading calculation candidates, and makes the remaining workflow,
correctness, boundary-data and performance work explicit.

The applicable gates are in [PROJECT_PLAN.md](PROJECT_PLAN.md), and source
movement remains governed by [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md).
Source/data classification, package licensing and generated-output project status
are governed by [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md).

## Evidence state

| Item | Value |
| --- | --- |
| Inventory date | 2026-07-19 |
| Inventory tool | `tools/phase1_inventory.py`, schema 2; adds static closure-cut caller and outgoing-dependency evidence to the earlier root/caller view |
| Plain-line oracle | `tools/freecad_bridge/ordinary_track_recipe.py`, schema 1 |
| Plain-line semantic SHA-256 | `b5641d79ff1fd77956f3ade8372da2f5b0dd50b6d42945aa611207242278b656` |
| Plain-line edit lifecycle/rollback oracle | `tools/freecad_bridge/ordinary_track_edit_recipe.py`, schema 2 |
| Initial complete-document semantic SHA-256 | `ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13` |
| Right-hand plain-line semantic SHA-256 | `4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4` |
| Plain-line selected-export oracle | `tools/freecad_bridge/ordinary_track_export_recipe.py`, schema 1 |
| Plain-line logical export SHA-256 | `91922662487f92b8bdb8f92a65e09fb7b62f2f9d1461704bb7c8cd41c2a15413` |
| Plain-line create-time logical export SHA-256 | `b33a2c5cfb6937d988046ad17584ed7bc2957514e77213282dfd665960bc4ffb` |
| Plain-line export production-metric SHA-256 | `37dcbc20e8ecda9c1a80b3e73646b0c1127211e01488d56eeef49aa08d0789b4` for selected and create-time paths |
| Plain-line create-time document SHA-256 | `a6aae6d70610ceec50a6223328db1454eca264effc12e7db5df07204707b3aa2` |
| Diagnosed create-time partial-directory SHA-256 | `05d27a32b26435eda3b776498c2b28195a943bc2499ced404450f18ce349bf29` |
| Connected straight/stationing oracle | `tools/freecad_bridge/straight_station_recipe.py`, schema 1 |
| Created `600/600 mm` straight/station workflow SHA-256 | `f5bf185baf2c61fbdf79c483b96ccf53e3a6206320e50087568e457022958a6c` |
| Edited `750/450 mm` straight/station workflow SHA-256 | `430d5f134e20789ee22c7f5549b64611a067646f1d24e038d4fbbc473d6b7666` |
| Standalone-turnout lifecycle oracle | `tools/freecad_bridge/turnout_recipe.py`, schema 1 |
| Created left-hand/facing turnout semantic SHA-256 | `0738c5a639618739c69fcd06553ea0584c5bf8c51253c330e3374f39e437c1cb` |
| Edited right-hand/facing turnout semantic SHA-256 | `46225072b4b56f7f767570c8b438ee0942c239f73f121ce420aa76caed9779f0` |
| Crossover feasibility oracle | `contracts/phase1-crossover-feasibility.json`, schema 1 |
| Crossover witnesses | `500.000 mm` preview-pass/complete-fail; `746.298 mm` complete-pass on the fixed curved-host fixture |
| Crossover automatic-timbering oracle | `contracts/phase1-crossover-timbering.json`, schema 1; reusable semantic helpers plus fast and disposable-FreeCAD validators |
| Fixed `XO-001` timber semantics | 86 effective records, 16 shared-envelope records, no unresolved or production conflicts; exact reuse/history/persistence evidence plus three bounded legacy defects |
| B14 role | Immutable legacy comparison oracle |
| B14 SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 role | Accepted behavioural reference |
| B15 SHA-256 | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| Chair source evidence | ignored Templot5 revision 556b SourceForge archive recorded in [PROVENANCE.md](PROVENANCE.md) |
| Chair source-audit date | 2026-07-20; read-only review of selected Pascal units |
| Source/data/output policy | explicitly accepted by the project owner on 2026-07-20; [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md) |
| Dependency/project-status manifest | `reference/schemas/dependency-manifest-v1.schema.json`, schema 1; enforced by `tools/validate_dependency_manifest.py` |
| First S1 pilot control manifest | structurally valid `unknown`; deliberately fails `--require-project-cleared` pending evidence, permissions, licence, non-copyright reviews and final package acceptance; the accepted Phase 1 control does not alter that status |
| First S1 pilot decision plan | `reference/S1_PILOT_PLAN.md`; owner accepted on 2026-07-22 as the blocked neutral package, quantity/frame, version/failure, evidence, intended-use and metric-family control, with all unsupported production decisions still blocked |
| First S1 pilot plan validator | `tests/validate_phase1_s1_pilot_plan.py`; protects the acceptance record, 15-decision register, exact B14/B15 source, unknown manifest, blocked lineage/oracle and absence of a premature production schema |
| Lineage audit scopes | first S1; core rail/timber used by S1; other S&C output; legacy B14/B15 output |
| First-S1/core lineage register | `reference/lineage/phase1-s1-core-lineage.json`, schema 1; 16 current output-affecting groups, all `reference-only` or `unknown`, with both scopes visibly `blocked` |
| First-S1/core lineage contract | `tests/validate_phase1_s1_lineage.py`; verifies register semantics, B14/B15 source anchors, the optional local archive hashes and the unresolved S1 manifest link |
| Other-S&C/legacy lineage register | `reference/lineage/phase1-other-snc-legacy-lineage.json`, schema 1; 24 bounded output-affecting groups, 14 `reference-only` and 10 `unknown`, with both scopes visibly `blocked` |
| Other-S&C/legacy lineage contract | `tests/validate_phase1_other_snc_legacy_lineage.py`; verifies the two remaining scopes, exact B14/B15 anchors, optional local evidence hashes, all-four-scope coverage and absent current output manifests |
| Candidate boundary register | `reference/contracts/phase1-candidate-boundaries.json`, schema 3; exact current contracts and closure-cut facts for all five static candidates plus the owner-accepted selection pointer |
| Candidate boundary contract | `tests/validate_phase1_candidate_boundaries.py`; verifies source/AST anchors, structural facts, transition/station schemas, chair record schemas, cache-signature inputs and fail-closed selected candidate |
| First-slice scorecard | `reference/PHASE1_SLICE_SCORECARD.md`; records why the transition solver was selected as a first architecture pilot, not a performance optimisation |
| Selected transition-pilot contract | `reference/contracts/phase1-transition-pilot.json`, schema 1; freezes B16/launcher identity, exact module/façade/caller boundary, expanded parity grid, rollback and profiling gates; Phase 2 foundation is authorised while calculation movement remains unstarted |
| Selected transition-pilot validator | `tests/validate_phase1_transition_pilot.py`; verifies exact B14/B15 source, signatures, constant, closure cut, generated parameter/error parity, evidence links and the current reserved-not-created package/launcher state |
| Runtime/legacy compatibility contract | `reference/contracts/phase1-compatibility.json`, schema 1; defines one exact qualified FreeCAD profile, the intended Addon manifest bounds, B14/B15 document ingress, external-configuration migrations and fail-closed unsupported-state rules |
| Qualified FreeCAD profile | Linux x86_64 stable `org.freecad.FreeCAD` Flatpak: FreeCAD 1.1.1, bundled CPython 3.13.14, PySide6/Qt 6.10.3, OpenCASCADE 7.8.1 and Coin 4.0.8 |
| Standalone development floor | CPython 3.12.0 minimum; observed repository environment 3.12.3. This qualifies tools/tests and future domain imports, not a FreeCAD host by itself |
| Compatibility probe and validator | `tools/runtime_compatibility_probe.py` emits a non-sensitive machine-readable record and exact-profile result; `tests/validate_phase1_compatibility.py` verifies source/schema anchors, current migration behaviour and fail-closed mutations |
| Legacy document ingress | B14-only, B15-only and the expected mixed B14/B15 version sets are the intended RC migration sources; implementation and entity-family fixtures remain Phase 4 work, so this is not a claim that a successor migrator exists today |
| Performance-boundary register | `reference/contracts/phase1-performance-boundaries.json`, schema 1; classifies nine controlled legacy profiles, all nested/harness spans, five bounded instrumentation defects and four unmeasured target-pipeline slots |
| Performance-boundary validator | `tests/validate_phase1_performance_boundaries.py`; verifies immutable source/report fingerprints, declared medians, per-run-before-median accounting, non-additive nested spans, source anchors, blocked optimisation/budget use and fail-closed mutations |
| Workflow-coverage register | `reference/contracts/phase1-workflow-coverage.json`, schema 1; all 14 canonical families have an accountable owner, known oracle state, repository evidence/control paths, visible gap owner and later closure phases |
| Workflow-coverage validator | `tests/validate_phase1_workflow_coverage.py`; cross-checks the Markdown table, exact B14/B15 fingerprints, 12 bounded-executed and two defined-blocked oracles, every referenced path and fail-closed mutations |
| Terminology-assurance register | `reference/contracts/phase1-terminology-assurance.json`, schema 1; 13 bounded term families across accepted, provisional, review-required and frozen-legacy states, six open reviews, three exact macro findings and 21 frozen evidence paths |
| Terminology-assurance validator | `tests/validate_phase1_terminology.py`; protects B14/B15 hashes and finding counts, the exact frozen path set, unresolved-review ownership and prohibited successor-product tokens while explicitly leaving semantic correctness to human review |
| Phase 1 closeout record | `reference/PHASE1_CLOSEOUT.md`; owner-accepted reconciliation of all nine exit conditions, runtime/ingress policy, GUI limitations, performance gaps, legacy defects, S1/provenance blocks, terminology reviews and bounded Phase 2 authority |
| Phase 1 closeout validator | `tests/validate_phase1_closeout.py`; protects the owning contracts, exact source hashes, accepted 10-decision register, mandatory later gates and bounded transition state |
| Project progress control | `PROJECT_PLAN.md` counts evidenced exit conditions and outcome milestones; `tests/validate_project_progress.py` reconciles bars, denominators, Phase 1 register states and milestone states without judging evidence sufficiency |
| Current B14/B15 project-control output status | group-level `reference-only` or `unknown`; no current other-S&C/legacy workflow has an output dependency manifest or positive status, and this is not a new output restriction |
| Production-source changes in this tranche | None |

The `ordinary_track` filenames, imports, commands and recipe IDs in this
inventory are frozen legacy evidence identifiers. Living prose follows
[TERMINOLOGY.md](TERMINOLOGY.md) and describes the subject as plain line.

The companion
[terminology-assurance register](contracts/phase1-terminology-assurance.json)
now makes human uncertainty explicit. It distinguishes six accepted bounded
term families, one provisional S1 description, five review-required semantic
families and the frozen ordinary-track identifier. Six open reviews have Phase
8 or Phase 9 owners and closure gates. Its scanner prevents known legacy terms
from silently entering future Workbench surfaces, but does not pretend that
word matching can decide railway semantics.

Reproduce the complete JSON inventory without importing or executing either
macro:

```bash
.venv/bin/python tools/phase1_inventory.py
```

Validate the analyser against a synthetic alias/patch fixture and both current
macros:

```bash
.venv/bin/python tests/validate_phase1_inventory.py
```

Validate ownership, oracle state and later gap closure for every canonical
release-critical workflow:

```bash
.venv/bin/python tests/validate_phase1_workflow_coverage.py
```

Validate the railway terminology-assurance states, source findings, frozen
identifiers, review ownership and successor scan:

```bash
.venv/bin/python tests/validate_phase1_terminology.py
```

Validate the accepted Phase 1 closeout aggregation and bounded transition:

```bash
.venv/bin/python tests/validate_phase1_closeout.py
```

Validate the executable dependency-manifest controls and the deliberately
unresolved S1 pilot record:

```bash
.venv/bin/python tests/validate_licensing_controls.py
.venv/bin/python tools/validate_dependency_manifest.py \
  reference/manifests/s1-chair-pilot.dependency-manifest.json
.venv/bin/python tests/validate_phase1_s1_lineage.py
.venv/bin/python tests/validate_phase1_other_snc_legacy_lineage.py
.venv/bin/python tests/validate_phase1_s1_pilot_plan.py
```

Run the first direct B14/B15 transition and station characterisation oracle:

```bash
.venv/bin/python tests/validate_phase1_alignment.py
```

Validate the five candidate boundaries and selected transition-pilot contract:

```bash
.venv/bin/python tests/validate_phase1_candidate_boundaries.py
.venv/bin/python tests/validate_phase1_transition_pilot.py
```

Validate the Phase 1 runtime and legacy-ingress contract, then inspect the
current standalone or FreeCAD runtime without exposing user paths:

```bash
.venv/bin/python tests/validate_phase1_compatibility.py
.venv/bin/python tools/runtime_compatibility_probe.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tools/runtime_compatibility_probe.py --pass --require-qualified
```

Run the fast contract checks for the deeper B14 plain-line document oracle:

```bash
.venv/bin/python tests/validate_phase1_ordinary_track.py
```

Capture the real FreeCAD oracle from one or more copied fixtures with:

```bash
tools/freecad_bridge/run-b14-ordinary-snapshot \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base.FCStd
```

Run the fast and real-GUI B14 plain-line edit lifecycle/rollback oracles with:

```bash
.venv/bin/python tests/validate_phase1_ordinary_edit.py
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Run the fast and real-GUI B14 plain-line selected-export oracles with:

```bash
.venv/bin/python tests/validate_phase1_ordinary_export.py
tools/freecad_bridge/run-b14-ordinary-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
tools/freecad_bridge/run-b14-ordinary-create-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Run the fast and real-GUI connected-straight/stationing lifecycle oracles with:

```bash
.venv/bin/python tests/validate_phase1_straight_station.py
tools/freecad_bridge/run-b14-straight-station \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Run the fast and real-GUI standalone-turnout lifecycle oracles with:

```bash
.venv/bin/python tests/validate_phase1_turnout.py
tools/freecad_bridge/run-b14-turnout \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The JSON is generated evidence rather than a committed snapshot. It contains
the source hashes, every top-level definition occurrence and provisional
responsibility signals, live static call edges, duplicate definitions,
captured callable aliases, module-level attribute patches, module calls,
mutable-state candidates and bounded caller/dependency maps. This document
commits the reviewed conclusions so a large generated dump does not become
repository bloat.

## Structural baseline

| Signal | B14 | B15 |
| --- | ---: | ---: |
| Source bytes | 2,242,840 | 2,286,863 |
| Newline count | 47,436 | 48,286 |
| Top-level function occurrences | 957 | 981 |
| Top-level class occurrences | 18 | 18 |
| Unique function/class names | 946 | 962 |
| Duplicate function names | 19 | 25 |
| Additional shadowing function occurrences | 26 | 34 |
| Duplicate class names | 2 | 2 |
| Additional shadowing class occurrences | 3 | 3 |
| Captured callable aliases | 20 | 27 |
| Module-level attribute/method patches | 30 | 31 |
| Module-level expression calls | 12 | 23 |
| Mutable-container bindings | 22 | 25 |
| Names assigned through `global` statements | 2 | 2 |

B14 has no final newline: its familiar `wc -l` value is 47,436 while
`splitlines()` exposes 47,437 logical lines. Both facts describe the same file
and hash.

B15 adds 24 top-level function occurrences, no class occurrence, seven captured
aliases, one direct method patch, eleven replacement workflow-registration
calls and three mutable-container bindings after the inherited B14 layer. The
existing full-AST parity test proves that the inherited layer is unchanged;
this inventory separately exposes the B15 overlay's runtime wiring.

### Interpretation

- A repeated name is not automatically dead code. Captured aliases retain
  earlier definitions and later functions call those aliases.
- The effective implementation depends on source execution order, global name
  lookup, captured aliases, direct class-method assignment and registration
  wrappers.
- Moving only the final definition of a repeated chair function would not
  mechanically preserve the current call chain.
- Static call edges resolve bare top-level calls and known captured aliases.
  Dynamic attribute calls, callbacks stored in containers and reflection still
  require targeted inspection and runtime evidence.

## Provisional responsibility and platform signals

The analyser applies deliberately broad, overlapping signals. They are an
inventory aid, not final module ownership: a mixed function can legitimately
appear in several columns, and a parameter named `doc` is only a boundary
signal until its type and use are reviewed.

| B15 responsibility signal | Definition occurrences |
| --- | ---: |
| Domain vocabulary | 581 |
| Application/workflow vocabulary | 149 |
| FreeCAD/document adapter signal | 315 |
| Export vocabulary | 77 |
| UI/Qt signal | 41 |
| Presentation vocabulary | 32 |
| Compatibility/version signal | 30 |
| Not classified by the static vocabulary | 200 |

| B15 direct boundary signal | Definition occurrences |
| --- | ---: |
| Document-like parameter | 253 |
| Direct `FreeCAD`/`App`/`Part`/`FreeCADGui` reference | 68 |
| Direct filesystem/export-support reference | 41 |
| Direct Qt reference | 31 |
| Direct subprocess reference | 1 |

The difference between 253 document-parameter signals and 68 direct FreeCAD
references is important. Some calculations accept FreeCAD-derived values
without naming FreeCAD, so source-level purity does not by itself prove a clean
serialisable domain boundary.

## Import-time and mutable-state map

B15 imports Python standard-library modules, then imports `FreeCAD` as `App`
and `Part` unconditionally. `FreeCADGui` is attempted under a guard, and the Qt
binding uses the existing PySide compatibility fallback. The final module-level
call is `run_macro()`.

Before launch, B15 executes 22 workflow-registration calls: eleven inherited
`_workflow_recorded_method(...)` calls and eleven B15
`_workflow_recorded_method_v15(...)` calls. It also contains 31 direct
attribute/method assignments. The principal patched classes are:

- `CrossoverManagerPanel` and `TurnoutManagerDialog`, whose guided actions and
  workflow update methods are replaced across the B12/B13 layers;
- `ChairAnalysisPanel`, whose construction, refresh, model-support and 2D-layout
  methods are assigned after class creation; and
- `GuidedTrackworkWorkflowPanel.__init__`, patched first by B14 and again by B15.

Consequently, importing the entire macro is itself UI/application composition.
Phase 2 must provide a separate package import boundary; it must not make a
purported domain module import the macro as a shortcut.

The 25 B15 mutable-container bindings include many catalogues and field lists
that are treated as constants in normal use. The stateful/high-risk subset is:

| Binding | Current users or mutation route | Risk to inventory |
| --- | --- | --- |
| `_CHAIR_SOLID_PLAN_CACHE` | Active `_chair_build_solid_plan` | Signature and invalidation ownership |
| `_CHAIR_2D_SYMBOL_CACHE` | `_chair_canonical_2d_symbol` | Process-lifetime representation reuse |
| `_CHAIR_PROTOTYPE_SHAPE_CACHE` | `_chair_make_s1_prototype_shape` | Exact `Part` shape retained globally |
| `_WORKFLOW_ACTIVE_MEASUREMENTS` | B15 workflow instrumentation | Nested measurement state |
| `_CROSSOVER_LAST_SOLVER_TRACE` | Reset and append helpers | Explicit global reassignment/mutation |
| `_PENDING_IMPORTED_CONFIGURATION` | Import-dialog hand-off | Explicit global reassignment |

The remaining mutable containers must still be reviewed for accidental writes,
but the analyser does not label a list or dictionary as harmful merely because
Python permits mutation.

## Duplicate and captured implementation map

B15 has 25 duplicate function names and two duplicate class names. The repeated
classes are `ChairAnalysisSettingsDialog` and `ChairAnalysisPanel`. The
function duplicates are concentrated in chair analysis, persistence,
presentation and B15 instrumentation:

`_chair_apply_physical_model_support`, `_chair_assignment`,
`_chair_build_solid_plan`, `_chair_connector_rail_records`,
`_chair_entity_objects`, `_chair_footprint_fit_measurements`,
`_chair_generation_context`, `_chair_orientation_metadata`,
`_chair_status_from_counts`, `_chair_turnout_rail_records`,
`_create_chair_2d_layout_display`, `_workflow_performance_report`,
`analyse_chair_position_records`, `analyse_entity_chair_positions`,
`build_and_validate_chair_2d_layout`, `chair_analysis_summary`,
`clear_chair_analysis_display`, `default_chair_analysis_settings`,
`generate_chair_positions`, `generate_supported_chair_solids`,
`invalidate_chair_analysis`, `normalise_chair_analysis_settings`,
`preflight_chair_analysis_readiness`, `prepare_chair_model_support`, and
`validate_chair_positions`.

The 27 callable aliases preserve several generations of behaviour. The most
important chains for a future chair extraction are:

- `_A8A7A1_VALIDATE_CHAIR_POSITIONS` retains the validator beginning at B15
  line 36,575; the active validator calls it and adds later findings;
- `_A8A7B11_*` aliases retain earlier metadata, display, invalidation,
  preflight and entity-analysis operations;
- `_A8A7B13_*` aliases retain pre-layout object, display, summary, panel and
  generation-context behaviour;
- `_A8A7B14_*` aliases retain the prior guided-panel constructor and rectangular
  2D display; and
- `_A8A7B15_*` aliases retain the B14 plan/support/layout/analysis/solid
  operations before B15 wraps them with caching and measurement.

This confirms that chair analysis is analytically promising but not a safe
first mechanical move based only on its final function bodies.

## Candidate-slice comparison

The table uses a two-call-deep dependency neighbourhood and a four-call-deep
reverse caller neighbourhood. Schema 2 distinguishes direct callers of the
nominated roots from external callers of **any** definition in that dependency
closure. It also reports calls leaving the bounded closure. Counts describe
static top-level definition occurrences, not runtime invocation frequency.

| Candidate | Roots | Dependency definitions / lines | Root callers | External closure callers | Outgoing dependencies | Caller closure | Platform signal | Existing position |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Curve/easement/station family | 3 | 6 / 154 | 35 | 65 | 0 | 114 | FreeCAD via station interpolation | Strategically broad; reject as one first move |
| Transition-length solver | 1 | 3 / 107 | 1 | 3 | 0 | 2 | None | Selected architecture pilot; exact contract frozen, source movement not started |
| Alignment station index | 1 | 1 / 25 | 15 | 15 | 0 | 77 | None directly | Foundational, but high fan-out and shallow FreeCAD-derived point inputs |
| Alignment station interpolation | 1 | 2 / 22 | 30 | 60 | 0 | 107 | Direct `App.Vector` construction | Split the coordinate record from the shared vector adapter first |
| Chair-analysis core | 4 | 39 / 1,396 | 18 B15 / 16 B14 | 39 B15 / 36 B14 | 11 | 57 B15 / 49 B14 | None in the bounded calculation closure | High-payoff later slice; not mechanically self-contained |

### Transition-length solver map

```text
prepare_track_alignment
        |
        v
solve_transition_length
        |
        v
transition_start_signed_offset
        |
        v
clothoid_entry_displacement
```

The three-function closure has no direct FreeCAD, Qt, filesystem, process,
mutable-global, duplicate-definition or captured-alias signal, and it has no
outgoing project-definition dependency. The root has one direct caller,
`prepare_track_alignment`, but a mechanical move of the complete closure has
three external callers because `clothoid_entry_displacement` is also used by
`main_circle_centre` and `build_concentric_core`. The direct characterisation
locks the default two-track outside solution, an inside solution, monotonic
targets, endpoint behaviour, invalid radius/range diagnostics and exact
B14/B15 equality. The project owner accepted this as the first architecture
pilot on 2026-07-20. The selected boundary reserves development checkpoint
`10.2A8A7B16` and the small future `TrackTemplate.FCMacro` compatibility
launcher in
[contracts/phase1-transition-pilot.json](contracts/phase1-transition-pilot.json);
package creation and source movement have not started.

### Station maps

`alignment_station_data` is a single 25-line function with fifteen immediate
and closure-cut callers. It builds cumulative station data from point objects
without directly importing FreeCAD. `interpolate_alignment_station` is only 20
lines, but calls the widely shared `vector_xy`, which constructs `App.Vector`;
including that adapter produces 60 external closure callers rather than the 30
root callers. This is a concrete boundary seam: station arithmetic can be
domain logic only when its point representation, units, frame and adapter
conversion are explicit.

The initial station oracle covers cumulative length, extension clamping,
negative/overrun station clamping, exact joints, interpolation, duplicate-point
ordering, incomplete inputs and B14/B15 equality. It intentionally preserves
the observed duplicate-station heading choice rather than declaring that choice
a future domain API before requirements review.

### Chair-analysis map

The current chair root set is `normalise_chair_analysis_settings`,
`generate_chair_positions`, `validate_chair_positions`, and
`analyse_chair_position_records`. Its two-deep closure contains 39 definitions
and no direct FreeCAD/Qt reference, which supports eventual domain extraction.
However, nine names in that closure are repeated, the two-deep closure still
has 11 outgoing definition dependencies, and 36 B14/39 B15 definitions call
into some part of it. The active validator
calls `_A8A7A1_VALIDATE_CHAIR_POSITIONS`. The four-deep caller map reaches
analysis metadata, displays, physical support, exact chair solids, UI classes,
guided workflows and B15 cache wrappers. Characterisation must therefore lock
down record schemas, ordering, findings, aliases, signatures and invalidation
before movement.

### Chair procedural-geometry source audit

The accepted B14/B15 relationship does not make the B15 supported chair body a
complete production-geometry oracle. B15 explicitly cites Templot5 556b
`init_2d_rea`, `init_3d_rea` and rail-section data, and
`_chair_s1_body_dimensions` preserves selected source dimensions. Its active
`_chair_make_s1_prototype_shape`, however, fuses five rectangular `Part` boxes
for the base edge, plinth, seat, inner jaw and outer jaw. Its readiness result
explicitly excludes keys, loose jaws/plugs and dedicated special-chair solids.
This is a bounded source-dimensional approximation, not a faithful procedural
S1 construction.

The read-only review of the local Templot5 revision 556b evidence finds a
different production model:

- Active `chairs_unit.pas` defines the `T_2d_data` and `T_3d_data` records.
  `init_2d_rea` and `init_3d_rea` populate full-size chair
  bases, corner radii, bolt centres, seat/plinth thicknesses, jaw sections,
  ribs, fillets, slopes, key and rail-fit/manufacturing parameters.
- Active `math_unit.pas` `drawtimber` resolves chair families and placements.
  Its nested `calc_fill_chair_outline`, `add_jaw`, `add_seat` and `add_key`
  paths build direct base geometry and constituent placement records referring
  to reusable blocks such as `S1OUTJAW`, `S1INJAW`, `S1SEAT` and `KEY`.
- `dxf_unit.pas` contains procedural component generators. For example,
  `create_s1_outer_jaw_block` connects parameterised top, middle, seat and
  plinth cross-sections, including sampled rib and fillet curves, with 3D
  faces. Related builders cover the other components and special chairs.
- `dxf_3dface`, `stl_3dface` and `insert_stl_block` form and triangulate the
  derived faces and place reusable component blocks at calculated transforms.
- `custom_3d_unit.pas` `.sk4` loading covers dimensional, rail and manufacturing
  settings; it is not evidence of a generic arbitrary-chair mesh importer.

The successor requirement is therefore source-informed procedural equivalence:
one versioned full-size chair definition feeds named constituent builders and
reusable transformed instances. FreeCAD/OpenCASCADE B-reps may replace
Templot's DXF-face implementation only when dimensional, component, interface,
topology and assembly comparisons pass. Neither the B15 boxes nor an imported
scan/mesh is canonical production geometry.

The bounded current-path map is now machine-readable in
[`lineage/phase1-s1-core-lineage.json`](lineage/phase1-s1-core-lineage.json).
It records 16 output-affecting groups across the S1 and shared rail/timber
paths: nine are `reference-only` because their present basis includes
unresolved Templot reference data, while source-expression compliance remains
a separate GPL question; seven are `unknown` pending an independent evidence
source or an accepted engineering/manufacturing decision.
The register freezes 27 literal/function source anchors in B14/B15 and hashes
the five reviewed active upstream units when the ignored local archive is
available.
It also makes the C10 timber-stationing path an explicit legacy interface,
not a hidden dependency of a reusable S1 definition.
The upstream S1 comments point to “Standard Railway Equipment 1926”; as
recorded in [PROVENANCE.md](PROVENANCE.md), this is an unverified search lead,
not selected primary evidence.

Phase 1 still needs an executed and reviewed S1 component/assembly oracle,
accepted primary evidence and agreed comparison metrics/tolerances. This audit
records structure, values, disposition and owners; it does not approve the
current values for a production package. No Templot code was copied into
production, no macro was changed and both registered scopes remain visibly
`blocked`.

### Other-S&C and legacy B14/B15 bounded lineage

The two remaining scopes are now machine-readable in
[`lineage/phase1-other-snc-legacy-lineage.json`](lineage/phase1-other-snc-legacy-lineage.json).
This is a group-level boundary and ownership map, not an assertion that every
historic constant has been independently cleared. Its 14 other-S&C groups
cover the current C10 rails and timbers, centreline-anchored lifecycle,
crossover connector and topology gates, automatic timber-resolution stages,
special-chair assignment, host integration and inherited export path. Its 10
legacy groups cover persisted/user state, retained FreeCAD shapes, all current
production formats and reports, B15 chair representations, output boilerplate,
external assets/exporters and the version/release boundary.

Fourteen groups are `reference-only` because their current output path includes
unresolved Templot reference data. Some also contain Templot source expression,
whose GPL compliance is tracked separately. Ten are `unknown` pending project
evidence or decisions. There is no `restricted` finding
because the reviewed record does not support that stronger classification, and
there is no `project-cleared` group. `chairs_unit_x.pas` is retained only to
explain the macro's historical citation; the register explicitly records that
it is an inactive alternate in the exact 556b project.

The contract test freezes 43 literal/function anchors across the exact B14 and
B15 hashes, checks five upstream members when the ignored archive is present,
and proves that the two lineage files together cover the four audit-scope IDs.
It also confirms that no current other-S&C or legacy output dependency manifest
exists. The later gates require an exact advertised workflow, field-level
lineage, embedded-material review, validated output manifest, non-copyright
reviews and owner acceptance. Completing an independently evidenced S1 package
will not silently clear the legacy macro or current special-trackwork output.

### Frozen S1 comparison-oracle capture contract

The next source-audit tranche is now executable without making an upstream
artifact canonical. The tracked
[`oracles/templot5-556b-s1-oracle.json`](oracles/templot5-556b-s1-oracle.json)
defines the exact-source fingerprints, proposed capture settings, named
constituents, local-only artifact policy, blockers, owners and minimum evidence.
[`../tools/templot_s1_oracle.py`](../tools/templot_s1_oracle.py) verifies that
contract and the ignored source archive, rejects a non-556b executable, and
summarises a future 3D DXF/ASCII STL pair using standard-library parsers.

The exact 556b source evidence establishes the required capture semantics:

- `dxf_unit.pas` defines `S1OUTJAW`, `S1INJAW`, `S1SEAT` and `KEY` reusable
  blocks before emitting entities;
- active `math_unit.pas` `drawtimber` records one of each named part for chair
  code 1, while the chair base/plinth contributes direct 3D faces; and
- the same constituent faces and placements are triangulated into the main
  ASCII STL, so DXF block/insert semantics and assembled STL bounds/facets are
  complementary evidence.

The project-file audit corrects an important earlier source-routing assumption.
`OpenTemplot2024.lpr` selects the mapped `math_unit.pas`, `pad_unit.pas`,
`chairs_unit.pas`, `dxf_unit.pas` and `custom_3d_unit.pas` paths; it does not
compile `math_unit_x.pas` or `chairs_unit_x.pas`.
Those `_x` files remain fingerprinted as inactive alternate copies only. They
must not be used to describe the executable 556b route unless a later exact
project file explicitly selects them. The oracle source probe and lineage test
now enforce this distinction.

The exact artifact is not yet available. A clean isolated native build probe
with Lazarus 3.0/FPC 3.2.2 stops at the Windows `ShellAPI` unit, and the ZIP is
not a self-contained build input: its README requires modified HtmlViewer
sources, its project references `FrameViewer09` and `synapse_units`, and those
inputs are absent from the archive. The existing local Bottles executable was
fingerprinted as SHA-256
`3df2cb480f828876967e5f7b5172111f5a1f1a159529c52a16456ebb627731f5`
and exposes version `5.55.a`; the validator rejects it rather than silently
substituting it for 556b. The everyday Templot bottle was not launched or
modified.

The finite unblock path is therefore: obtain or reproducibly build an exact
556b executable with its external dependencies recorded; run it only in a
disposable profile; create and hash one short S1-only plain-line fixture;
record every effective geometry/manufacturing setting; capture DXF and STL
locally under ignored `benchmark-output/`; set both normal and FDM key
off-centre limits to zero so Templot's random direction cannot move the key;
and pass the semantic inspector plus geometry/owner review. The inspector
requires non-empty faces for all four named blocks, equal non-zero assembly
insert counts, direct base/assembly faces
and a structurally complete ASCII STL. It deliberately reports
`semantically-valid-unaccepted-capture`: hashes establish provenance, not
geometric equivalence, and the capture remains comparison-only.

This completes the Phase 1 **recipe-and-explicit-blocker** branch of the oracle
deliverable. It does not claim that the frozen oracle itself exists, does not
clear any S1 production value, and does not close Phase 1.

### Active 556b S1 value and transform map

The remaining read-only chair-generation inventory is now machine-readable in
[`lineage/templot5-556b-s1-generation-map.json`](lineage/templot5-556b-s1-generation-map.json).
It is deliberately bounded to chair code 1 with solid jaws and records:

- the five mapped active Lazarus units and the two inactive `_x` alternatives;
- full-size-inch, model-millimetre, angle and output-unit boundaries;
- component-local, chair-on-timber, template-placement and output frames;
- eight field groups covering the S1 plan, selected rail section, common
  base/seat/key inputs, outer- and inner-jaw sections, placement and output
  compensation, including the otherwise stochastic key-offset policy;
- nine active stages from project-unit resolution and data initialisation to
  direct base faces, reusable constituent blocks, transformed placements and
  DXF/STL emission;
- the separate base/plinth, `S1OUTJAW`, `S1INJAW`, `S1SEAT` and `KEY`
  constructions; and
- seven manufacturing/output branch groups plus the evidence needed to close
  every unresolved or deliberately bounded finding.

[`../tests/validate_templot_s1_generation_map.py`](../tests/validate_templot_s1_generation_map.py)
fails closed if an inactive source copy is promoted, a Templot-dependent group
is marked project-cleared, the chair-code scope broadens, a component/frame
link drifts, or the acceptance gate is weakened. When the ignored ZIP exists,
it additionally verifies every mapped field/symbol against the exact member,
the active project-unit declarations, the code-1 constituent sequence and the
DXF/STL output route.

This completes the Phase 1 **source value/unit/frame/transform map** branch,
subject to project-owner review. All mapped fields and constituents remain
`reference-only`; the map authorises neither Pascal translation nor production
use. Independent S1 evidence, the neutral ChairDefinition, exact 556b
artifacts and accepted comparison tolerances remain later gates.

### Chair-definition assimilation scope

On 2026-07-20 the project owner accepted a release-candidate capability that
loads versioned chair-definition packages and proves one operator-assisted S1
assimilation pilot. All native and assimilated chairs must use the same domain
definition and exact generator. Source scans, CAD files, drawings and
measurements are provenance-bearing evidence used to fit a definition; they do
not form a parallel runtime geometry system.

The pilot must establish source calibration and frame, declared units and
scale, constituent segmentation, rail-interface landmarks, explicit measured
versus inferred values, residual comparison, unresolved findings, provenance
and manual acceptance. A scan alone is insufficient evidence for hidden or
worn surfaces, nominal dimensions, component boundaries and rail fit. Fully
automatic conversion of an arbitrary 3D source is consequently outside the RC
scope and remains post-RC research.

The owner-accepted [first S1 pilot plan](S1_PILOT_PLAN.md) now turns that
direction into 15 explicit decisions. It requires exact source-quantity
serialization, full-size millimetres, a right-handed gauge-to-field chair
frame and validate-before-mutation failure behaviour. It fixes the minimum
evidence bundle and comparison metric families without inventing dimensions or
tolerances. The precise designation, primary evidence, rail section,
constituents/landmarks, final package licence, rights reviews, numeric
tolerances and assimilation residual policy remain owner/evidence gates. The
plan was accepted on 2026-07-22; the actual package is not project-cleared.

### Source/data/output licensing boundary

The 2026-07-20 read-only evidence review now separates four matters that were
previously too easy to conflate:

- the Templot5 Pascal source and its GPL-3.0-or-later notices;
- established engineering methods and independently evidenced factual values;
- Templot-authored tables, profiles, value collections and generated media;
  and
- the rights dependencies of TrackTemplateMacro-generated output.

The reviewed 556b print/PDF paths stamp a copyright assertion about design
elements and data in Templot drawings. The snapshot contains no general CC
BY-NC-SA or non-commercial output licence; its Creative Commons wording is
specific to imported National Library of Scotland maps. Historical Templot2
terms and forum-uploaded-media terms are recorded separately in
[PROVENANCE.md](PROVENANCE.md) rather than treated as the current GPL source
licence.

The accepted successor boundary is a neutral `ChairDefinition`. Engineering
facts, project measurements and project derivations require their own evidence
chain; a Templot comparison can be an oracle but cannot silently become their
claimed primary source. Templot reference data/media remains local and
untracked unless its exact redistribution and output use is accepted. Any
future Templot-format support is a one-way outward adapter and cannot feed
opaque media or unreviewed values back into canonical state.

The red-team follow-up converts that policy into executable controls. The
positive internal status is now `project-cleared`, explicitly not a legal
opinion. A Draft 2020-12 JSON Schema and standard-library validator fail closed
when any output-affecting dependency is unresolved, `NOASSERTION`, lacks the
declared adaptation, production, redistribution, commercial-use or publication
permission, lacks authority evidence, or has an incomplete registered-design,
unregistered-design, patent or trade-mark review.
[`CONTRIBUTING.md`](../CONTRIBUTING.md) adds prospective DCO 1.1
sign-off and a separate data/evidence declaration.

The first S1 manifest is intentionally useful before it is clear: it records
the unselected primary evidence as `unknown`, Templot5 as non-output-affecting
`reference-only`, and every unperformed non-copyright review. It validates as
a truthful control record but fails the strict `--require-project-cleared`
gate. No package or output can receive the positive status without that strict
validation.

The first-S1 and core rail/timber current paths now share a validated bounded
register. It deliberately takes the gate's blocked branch: no entry is
`project-cleared`, the existing Templot-dependent values remain comparison
evidence, and the unselected S1 evidence and package rights stay `unknown`.
Resolving an entry requires new evidence or an explicit accepted decision; it
must not be cleared by editing the register alone. The other S&C and legacy
B14/B15 registers are still required with current statuses, owners and later
gates. Current B14/B15 output remains `unknown` for project control and is not
retroactively labelled unrestricted by this documentation change.

## Release-critical workflow coverage inventory

This is the canonical human-readable owner/coverage map. “Gap” means the
behaviour must be characterised before its legacy path is moved or the future
capability is advertised; it does not imply the workflow is known to be
defective. The fail-closed machine-readable control is
[`contracts/phase1-workflow-coverage.json`](contracts/phase1-workflow-coverage.json).

| Workflow family | Current oracle/evidence owner | Deterministic recipe or fixture | Principal Phase 1 gap |
| --- | --- | --- | --- |
| Curve/easement creation and editing | B15 reference; B14 oracle; direct transition/station characterisation; fixed create-result, edit-lifecycle, selected-export and create-time-export oracles | B14 default-base builder plus the four `run-b14-ordinary-*` characterisation wrappers | Fixed left/right replacement, undo/redo, exact change-back, persistence, negative paths and both export entry points for retained/fresh exact shapes are characterised; wider curve boundaries and future deferred Validate/reconstruction remain open; remaining curve functions lack direct oracles |
| Straight/stationing workflow | B15/B14 source plus direct calculation parity and the connected-pair lifecycle oracle | `run-b14-straight-station` creates and edits a deterministic entrance/exit pair from the fixed two-track curve | Connected route inputs, identities, inherited track order, travel-order stationing, joins/tangents, length editing, complete history recovery, raw persistence, exact document shapes and ordered production catalogue are characterised; the independent-datum GUI, physical station/platform, straight file export, straight-specific failures and wider configurations remain open |
| Multiple-track/spacing transition | Default B14 two-track base fixture plus deep create/edit/export document oracles | `build-b14-base` plus the four `run-b14-ordinary-*` characterisation wrappers | The fixed two-track configuration survives handedness replacement/reopen, selected export and create-time export; deferred Validate/reconstruction plus spacing/easement edit and invalid-input edge cases remain open |
| Standalone turnout | B15/B14 calculation parity plus B14's complete fixed-lifecycle semantic oracle | `run-b14-turnout` creates `TO-001` on persisted Main Track identity at chainage `746.298 mm`, edits its hand and exercises recovery | Curved-host left/facing creation, one handed edit, exact history/persistence, overlap rejection and injected transaction abort are characterised; trailing GUI orientation, straight/other hosts, wider inputs, removal/integration, downstream timber/chair stages and export remain open |
| Crossover geometry | B14 cold series, B15 acceptance report and the fail-closed crossover-feasibility contract | Controlled `XO-001` bridge recipe plus read-only `500.000/746.298 mm` analytical witnesses on the fixed curved-host fixture | The current preview/commit mismatch is quantified; shared successor preflight, zero-mutation early rejection, exact-build agreement, create/edit/extend GUI regression and wider arrangements/hosts remain open |
| Automatic timbering | Controlled `XO-001` workflow plus the fail-closed semantic/lifecycle contract | Crossover cold recipe and disposable `freecad_validate_phase1_crossover_timbering.py` copy | Fixed curved-host records, calculation invalidation, reuse, Undo/Redo, persistence, clear and injected failure are characterised; persisted-analysis drift, display-only over-invalidation and abort cleanup remain successor defects; standalone turnout/plain-line decisions, wider crossover inputs and the complete invalidation matrix remain open |
| Chair analysis and 2D presentation | B15 analytical tests, B14-to-B15 acceptance and the fail-closed persistence plus invalidation contracts | Disposable post-B4 `XO-001` built from the regenerated base fixture, plus the controlled completed GUI document | Fixed cold/reuse/history/reopen semantics, all emitted input fields, representative mutations, an actual stale-cache hit and headless presentation topology are characterised; upstream config-to-record mutation, successor fixes, turnout/plain-line/wider crossover coverage and lightweight real-GUI semantics remain open |
| Legacy approximate supported chair bodies | B15 smoke and acceptance | Completed `XO-001` acceptance path | Late reuse check, each solid-signature invalidation class and export-scope coverage; five-box S1/S1J bodies are gap evidence, not the final procedural chair oracle |
| Procedural chair definitions and exact components | Templot5 556b source audit, accepted architecture/licensing boundaries, blocked first-S1/core lineage register and fail-closed S1 oracle contract | Exact source/member hashes and constituent route are reproducibly verified; capture settings and semantic DXF/STL checks are defined, but the exact 556b executable, S1-only fixture and artifacts remain blocked | Execute and review the frozen local Templot S1 capture; define the neutral package schema; obtain rights-compatible primary evidence, accepted full-size values/transforms, package licence, comparison metrics and tolerances |
| Assisted chair assimilation | Accepted RC scope; no implementation oracle yet | One S1 pilot to be selected | Precise prototype designation, evidence provenance/rights, intended commercial/publication use, calibrated scan/CAD/measurement set, component landmarks, fit-residual policy, package licence and acceptance recipe |
| Host integration | Controlled crossover acceptance | `XO-001` stage 6 | Standalone turnout, removal/reversal, rollback and legacy-document variants |
| Save/reopen | B15 crossover acceptance and B14 plain-line edit-lifecycle oracle | Accepted B15 FCStd copy/reopen sequence plus `run-b14-ordinary-edit` | Broader entity families and future schema migration |
| SVG/DXF/STL/STEP and manifests | B14 source paths plus fixed plain-line selected- and create-time-export oracles | `run-b14-ordinary-export` covers revision/overwrite/atomic rollback; `run-b14-ordinary-create-export` covers the normal Generate entry point, all four formats, manifest, persistence and final-task failure | Cancellation, other scopes/entity families, accepted create-time all-files rollback, future deferred exact-shape reconstruction, output-specific other-S&C/legacy lineage closure and integration of the dependency/project-status manifest |
| Failure recovery | Transactional source paths, strict bridge dialog policy, plain-line edit lifecycle and both export fault injections | Edit oracle proves zero-angle rejection/post-removal abort and bounds B14's three-entry incomplete Undo states; selected export proves byte restoration; create-time export freezes the current 13-file partial result and unchanged document | Make successor edit commands and create-time output atomic under accepted contracts; add equivalent fixtures for other release-critical workflows |

The register contains the same 14 workflow identities. Twelve current or
cross-cutting families point to bounded executed evidence; procedural chair
definitions and assisted chair assimilation are `defined-blocked` because
their acceptance oracles are specified but their S1 evidence and owner
decisions are not yet available. Every row retains a gap owner and later
closure phase. This evidences the Phase 1 ownership/oracle/gap condition; it
does not execute or waive those later gates.

Existing crossover evidence remains owned by
[benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md),
[benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md),
and
[benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md](benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md).
The fixed preview/complete-rule mismatch and successor acceptance boundary are
recorded in
[contracts/phase1-crossover-feasibility.json](contracts/phase1-crossover-feasibility.json)
and
[benchmarks/2026-07-21-b14-crossover-feasibility-characterisation.md](benchmarks/2026-07-21-b14-crossover-feasibility-characterisation.md).
The fixed automatic-timbering calculation, reuse, history, persistence,
display-only invalidation and injected-failure boundary is recorded in
[contracts/phase1-crossover-timbering.json](contracts/phase1-crossover-timbering.json)
and
[benchmarks/2026-07-21-b14-crossover-timbering-characterisation.md](benchmarks/2026-07-21-b14-crossover-timbering-characterisation.md).
The fixed post-B4 chair-analysis result, persistence, unchanged-reuse history,
diagnostic-display identity and save/reopen boundary is recorded in
[contracts/phase1-chair-analysis-persistence.json](contracts/phase1-chair-analysis-persistence.json)
and
[benchmarks/2026-07-21-b14-chair-analysis-persistence-characterisation.md](benchmarks/2026-07-21-b14-chair-analysis-persistence-characterisation.md).
Its complete fixed-XO emitted-input classification, representative mutation
matrix, stale-cache witness, signature precision/order behavior and headless
presentation topology are recorded separately in
[contracts/phase1-chair-analysis-invalidation.json](contracts/phase1-chair-analysis-invalidation.json)
and
[benchmarks/2026-07-21-b14-chair-analysis-invalidation-characterisation.md](benchmarks/2026-07-21-b14-chair-analysis-invalidation-characterisation.md).
The plain-line edit, persistence and rollback evidence is recorded in
[benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md](benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md).
Its undo/redo and explicit change-back extension is recorded in
[benchmarks/2026-07-19-b14-plain-line-edit-lifecycle-series.md](benchmarks/2026-07-19-b14-plain-line-edit-lifecycle-series.md).
The plain-line selected-production export evidence is recorded in
[benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md](benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md).
The normal Generate-path production-export evidence is recorded in
[benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md](benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md).
The connected-straight creation, stationing, edit, history, persistence and
production-catalogue evidence is recorded in
[benchmarks/2026-07-20-b14-straight-station-workflow-series.md](benchmarks/2026-07-20-b14-straight-station-workflow-series.md).
The standalone-turnout creation, handed edit, history, persistence, overlap-
rejection and transaction-abort evidence is recorded in
[benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md](benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md).

## Fixed plain-line document contract

The Phase 0 fixture hash remains unchanged and intentionally small because it
is the crossover-recipe precondition. Phase 1 adds a separate deeper oracle.
In one isolated FreeCAD 1.1.1 run, the original 641,206-byte fixture and the
independently regenerated 636,344-byte fixture had distinct binary SHA-256
values but the same base semantic hash and the same deep semantic SHA-256
`b5641d79ff1fd77956f3ade8372da2f5b0dd50b6d42945aa611207242278b656`.

The deep contract establishes:

- nine named objects and exact group membership, with `SET-001` as the shared
  template-set identity and track numbers 1 and 2 as the plain-line centreline
  identities;
- 38 mirrored typed configuration/calculated properties on settings and
  template, plus settings-only `ProductionRecordIndexJSON` (39 properties on
  settings); lengths use `App::PropertyLength` in millimetres and angles use
  `App::PropertyAngle` in degrees;
- ordered JSON arrays remain ordered, while the generated disabled-platform
  `manager_id` and production-index `created_at` retain their schema keys but
  are replaced by explicit placeholders for comparison;
- four ordered production records: hidden 2D template cutting profile, direct
  3D template solid, Main Track centreline engraving and Track 2 centreline
  engraving, each with its complete stable record ID and supported formats;
- global XY plan geometry, positive-Z template thickness, valid topology,
  measures and bounds without relying on FreeCAD's process-sensitive shape
  hash codes; and
- the current exact-shape cost already present in the editable fixture: the
  template compound has 2 solids, 2,104 faces and 6,300 edges; its hidden 2D
  production source has 2,100 edges; the two centreline wires have 515 and 533
  edges. These are structural observations, not performance timings.

It also exposes a small but important representation boundary. The persisted
main length and direct centreline-wire length round to `1542.476831 mm`, while
the special-trackwork host reconstruction used by the Phase 0 base check rounds
to `1542.475839 mm`; Track 2 is `1627.288494 mm` versus `1627.287516 mm`.
Those differences are about one micrometre. The oracle retains both values:
Phase 1 must identify the sampling/conversion source and agree the applicable
tolerance before a modular API treats these representations as interchangeable.

The oracle discovered and now protects two FreeCAD-specific facts rather than
papering over them: a null `Part` shape raises if validity/type analysis is
attempted, and the production-record index is not mirrored onto the template.
The companion edit and export oracles now cover the fixed right-hand
replacement, undo/redo, exact explicit change-back, both current export entry
points and bounded failure paths. Broader parameter boundaries and deferred
Validate/reconstruction remain open.

## Plain-line editing lifecycle, persistence and rollback contract

The isolated `run-b14-ordinary-edit` recipe uses B14's real curve dialog and
normal replacement path on a disposable copy of the fixed left-hand fixture.
The original three-run replacement/rollback series and the v2 three-run
lifecycle extension all produced right-hand semantic SHA-256
`4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4`
before and after their applicable history, persistence and failure actions.
The source fixture remained byte-identical in every run.

The contract establishes:

- plain-line inputs are reloaded from the persisted document when
  remembered UI state is absent, and the fixed dialog's three-decimal
  `559.410 mm` transition display maps back to the existing exact solved
  `559.410254727028 mm` persistence value;
- replacing `+90°` with `-90°` retains all nine stable objects, grouping,
  production-record ordering, property types, topology and measures;
- the template, hidden production source and two centrelines reflect their Y
  bounds exactly, while the only changed persisted fields on settings and
  template are `CircularArcAngle`, `TotalTurnAngle`, `TransitionAngleEach` and
  `TurnDirection`;
- one logical B14 replacement produces three FreeCAD history entries, newest
  first: material report, production schedule, and curve/straight production
  templates. Successive Undo operations expose eight objects, then seven,
  before the third restores the complete preceding nine-object state; Redo
  mirrors the sequence;
- explicitly changing `-90°` back to `+90°` restores the exact initial
  complete-document SHA-256
  `ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13`,
  and three Undo operations then recover the exact right-hand state;
- save/close/reopen preserves the complete right-hand state and resets the
  document's observable undo/redo counts to zero;
- the exact zero-angle diagnostic occurs before transaction opening and leaves
  the complete document semantic hash unchanged; and
- an injected failure at the first generated-object tagging call occurs after
  old generated outputs have been removed inside the transaction, exercises
  B14's real `abortTransaction()` path, and restores the complete document
  semantic hash and nine-object inventory.

The source-order audit also records an important boundary for future
modularisation: B14 remembers accepted dialog and material-report preferences
before validation and before the FreeCAD document transaction. Failed actions
therefore retain attempted UI inputs while rolling back document state. Tests
must not conflate these two behaviours. The isolated recipe validates the
remembered payloads after every history action and then restores its
development profile.

The three-entry edit stack is a bounded B14 atomicity defect, not an accepted
parity requirement. The successor contract requires one accepted application
command to be one complete undo unit, including production-schedule and
material-report refresh, so one Undo cannot expose an incomplete document.

The original successful replacement action had a three-process median wall time of
`2781.596 ms` (range `2769.362–2836.972 ms`) and median RSS change of
`+234.840 MB` (range `+182.641–+299.961 MB`). Explicit recompute/save/reopen
then had a `758.005 ms` median. The v2 series independently observed a
`2783.694 ms` replacement median and a later same-process `2044.726 ms`
explicit change-back median. Its three-step action-plus-recompute medians were
`6.724 ms` for Undo, `1.824 ms` for Redo and `2.722 ms` for undoing
change-back. Deep semantic validation took roughly 1.2 seconds per history
step and is harness cost, not operator-visible Undo/Redo time. These are
characterisation measurements, not accepted interaction budgets or a
lightweight-view profile. Exact recipes, individual results and limitations
are in the two benchmark reports.

## Plain-line selected production export contract

The isolated `run-b14-ordinary-export` recipe drives B14's real
`SelectedProductionExportDialog` against a disposable copy of the fixed
left-hand fixture. Three fresh FreeCAD 1.1.1 processes produced the same
logical 14-file SHA-256
`91922662487f92b8bdb8f92a65e09fb7b62f2f9d1461704bb7c8cd41c2a15413`
for initial output, `_Rev_02` repeat and confirmed overwrite. Every action left
the document at nine objects with semantic SHA-256
`ed6021762297912796c93c3c126b9b86c62d56f52287d237c90075414c7ebd13`.

The contract establishes:

- the complete `SET-001` scope resolves the fixture's four ordered production
  records into 13 tasks and one manifest: five DXF, five SVG, one STL, two STEP
  and one CSV file;
- the 21-column manifest contains 15 success rows, no failure/skip row and all
  four requested production formats;
- non-overwrite repeat creates exactly `_Rev_02` and preserves every base file
  byte, while confirmed overwrite replaces a deliberate sentinel and
  preserves every revision file byte;
- known path/time, allocator and exporter-instance metadata is normalised for
  logical comparison, while raw hashes, DXF/SVG parsed bounds, STEP topology
  and STL mesh metrics remain independently checked; and
- a failure injected inside the real commit after one destination replacement
  exercises backup restoration, leaves the complete 28-file raw-hash map
  unchanged and leaks no staging directory.

The first selected-export action had a three-process median wall time of
`7885.730 ms` (range `7788.967–7991.619 ms`) and median RSS change of
`+134.996 MB` (range `+131.543–+157.281 MB`). Its staged
write/commit/cleanup transaction was `3084.831 ms` median, while three full
DXF/SVG probe preflights consumed a combined `4035.036 ms` median. The action
made 43 exporter dispatches for 13 deliverables. These are measured legacy
costs, not approved interaction budgets; the repeated probes are now an
explicit optimisation candidate whose validation and late-path safety
contracts must be preserved.

This is the atomic explicit selected-export path. The separate create-time
contract below prevents its stronger transaction semantics being inferred for
the normal Generate action.

## Plain-line create-time production export contract

The isolated `run-b14-ordinary-create-export` recipe drives the real curve
dialog and normal replacement path with production export enabled. Three fresh
FreeCAD 1.1.1 processes all produced normalised document SHA-256
`a6aae6d70610ceec50a6223328db1454eca264effc12e7db5df07204707b3aa2`
before save and after reopen. The fixed success directory contains 14 files
with logical SHA-256
`b33a2c5cfb6937d988046ad17584ed7bc2957514e77213282dfd665960bc4ffb`.

The create-time serialisation hash differs from selected export for five SVG,
two STEP and one STL file, while all parsed bounds, topology and mesh measures
match exactly under shared metric SHA-256
`37dcbc20e8ecda9c1a80b3e73646b0c1127211e01488d56eeef49aa08d0789b4`.
The distinction is preserved rather than hidden by broader normalisation.

The recipe also injects one failure at the final combined-solid STEP task.
B14 retains twelve task files and the manifest, reports 13 successful files
and one failure, and writes a 15-row manifest with 14 success rows and the
exact failure row. The stable 13-file directory hash is
`05d27a32b26435eda3b776498c2b28195a943bc2499ced404450f18ce349bf29`;
the document remains valid and no temporary object/file leaks. This bounds the
legacy behaviour but does not accept non-atomic output as the migration
contract. The later overall dialog's “created successfully” wording despite
the disclosed failure is a related open correctness/UI obligation.

The comparable successful Generate-through-export action has a three-process
median wall time of `6907.971 ms` (range `6886.804–6984.403 ms`) and median RSS
change `+259.992 MB` (range `+258.719–+264.113 MB`). Its single complete
exporter-bound preflight is `1450.616 ms` median and the actual export is
`2883.880 ms` median. These are bounded legacy measurements, not accepted
human-use budgets. Full evidence and limitations are in the benchmark report.

## Connected straight and stationing contract

The isolated `run-b14-straight-station` recipe invokes B14's real controlled
curve-entrance/curve-exit pair action on the fixed two-track curve. Three fresh
FreeCAD 1.1.1 processes produced created `600/600 mm` workflow SHA-256
`f5bf185baf2c61fbdf79c483b96ccf53e3a6206320e50087568e457022958a6c`
and edited `750/450 mm` workflow SHA-256
`430d5f134e20789ee22c7f5549b64611a067646f1d24e038d4fbbc473d6b7666`.

The analytical boundary now establishes that each connected route inherits
Main Track then Track 2 with the exact source endpoint, tangent, width and
output choices. Entrance station zero is the remote end and station `L` is the
curve join; exit station zero is the curve join and station `L` is the remote
end. Every characterised join has zero normalised endpoint and heading error.
The manager IDs persist exactly in raw Settings and Template JSON and produce
stable `straight-<manager_id>` route IDs.

The normal Generate action materialises a 23-object document and an ordered
12-record catalogue. Full three-entry Undo/Redo cycles recover the exact base,
created and edited states; save/reopen preserves the complete edited payload;
and changing only straight lengths leaves the exact curve template and
centrelines unchanged. The three-entry schedule/report/geometry stack is the
same bounded B14 atomicity defect already recorded for curve editing, not a
successor requirement.

The fast oracle also covers one independent reverse/right-side two-track datum
and exact B14/B15 calculation parity. The independent-datum GUI, physical
station/platform, straight target-file export, formation/section options and
straight-specific negative paths remain open. Full evidence and timings are in
[benchmarks/2026-07-20-b14-straight-station-workflow-series.md](benchmarks/2026-07-20-b14-straight-station-workflow-series.md).

## Standalone turnout lifecycle contract

The isolated `run-b14-turnout` recipe drives B14's real turnout manager on a
copy of the fixed two-track curve. It resolves `SET-001` Main Track from its
persisted identity, places `TO-001` at host chainage `746.298 mm`, and creates
a left-hand REA C10 facing in host travel direction. Three fresh FreeCAD 1.1.1
processes produced created semantic SHA-256
`0738c5a639618739c69fcd06553ea0584c5bf8c51253c330e3374f39e437c1cb`
and, after changing only the hand to right, semantic SHA-256
`46225072b4b56f7f767570c8b438ee0942c239f73f121ce420aa76caed9779f0`.

The document grows from 9 to 17 objects. Eight stable turnout roles share the
same typed `TO-001` configuration, retain their names across the handed edit,
and add six ordered production records after the four inherited curve records.
The exact curve Template, Centrelines and ProductionSource geometry remains
unchanged. Both the single-entry creation and edit transactions recover their
complete before/after states through Undo/Redo, and save/reopen preserves the
right-hand hash with cleared history.

The recipe also proves that a second turnout at the occupied chainage is
rejected before document/history mutation and that an injected first-mutation
failure inside an edit restores the exact accepted state through
`abortTransaction()`. The fast oracle freezes representative REA C10 values,
valid toe/occupied intervals, handing/orientation mappings and exact B14/B15
calculation parity. The captured values and shapes remain a B14 legacy
comparison oracle, not project-cleared canonical production data.

The three-run median creation wall time is `1743.967 ms` and handed-edit wall
time is `1977.051 ms`, with median end-minus-start RSS changes of `+54.738 MB`
and `+43.438 MB`, respectively. These are bounded legacy observations, not
accepted human-use budgets. Trailing orientation through the GUI, straight or
alternate hosts, wider gauge/flangeway/output choices, removal/integration,
standalone timber/chair stages, target-file export and deferred reconstruction
remain open. Full evidence and limitations are in
[benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md](benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md).

## Candidate boundary-data contract

The five candidates emitted by the static inventory now have an exact,
machine-readable current-state contract in
[contracts/phase1-candidate-boundaries.json](contracts/phase1-candidate-boundaries.json).
It records inputs, outputs, units, frames, tolerances, identity and ordering
rules, side effects, errors, schemas, cache/signature behaviour, current
oracles, structural facts and open extraction gates for:

- the comparison-only curve/easement/station aggregate;
- the transition-length solver;
- the cumulative alignment-station index;
- alignment-station interpolation; and
- the chair-analysis core and its surrounding application cache boundary.

The fail-closed validator ties those statements to both complete macro
fingerprints, 30 literal/function anchors and the live schema-2 AST inventory,
including closure-cut caller and outgoing-dependency counts. It also
derives the seven-field station schema and the current chair settings, rail,
timber, position, finding, support-plan, summary, result and signature payload
schemas directly from source. It records rather than hides the one anchored
B14/B15 difference in the first chair application wrapper.

The evidence makes the trade-off clearer. The transition-length solver is the
selected structural leader: one root caller, three external closure callers, a
three-definition platform-free/self-contained closure and a direct numerical
oracle. The scorecard and accepted contract make it a first architecture
pilot, not a performance optimisation or authority to start source movement.
The station index has high fan-out; interpolation still returns `App.Vector`; and
the chair core has duplicate/alias coupling, non-deterministic timings and
unvalidated mapping inputs. Its fixed-XO signature omissions, precision alias
and order over-invalidation are now classified by the dedicated invalidation
contract. Those defects must be fixed before a migrated cache treats a
matching signature as semantic equivalence.

This closes the bounded **candidate boundary-recording** task. It does not
complete the wider curve-to-export boundary inventory: production-file units,
exact-solid/export signatures, chair-definition package and constituent
schemas, and all workflow invalidation/change-back cases still belong to their
own release-critical paths and gates. The static inventory remains a location
map; the new register is the semantic current-state contract for only the five
listed candidates.

## Performance inventory status

The controlled crossover cold/warm series identifies genuine dominant costs.
The plain-line edit series separately records the full exact-shape
left-to-right replacement boundary at a `2781.596 ms` median and subsequent
recompute/save/reopen at `758.005 ms`; the v2 lifecycle series reproduces the
replacement at `2783.694 ms`, records explicit change-back at `2044.726 ms`,
and separates sub-7 ms three-step history action/recompute totals from its
roughly 1.2-second-per-state deep-oracle cost. The selected-export series adds a
`7885.730 ms` cold action median for the fixed retained exact shapes and splits
that into repeated probe preflights versus the staged transaction. The
create-time series adds a `6907.971 ms` median fixed Generate-through-export
boundary, including fresh legacy exact-shape construction, one complete
preflight and non-staged export. The standalone-turnout series adds a
`1743.967 ms` median fixed left/facing creation boundary and a `1977.051 ms`
median handed-edit boundary, plus exact rejection/abort/history/persistence
evidence. None measures a proposed lightweight editor or deferred
Validate/rebuild, so Phase 1 still lacks a reconciled curve-to-export target-
architecture profile.
Before profiles select an optimisation, the defects already recorded in
[VALIDATION.md](VALIDATION.md) must be closed or bounded:

1. geometry external/internal timing boundary gap;
2. prematurely persisted chair timing payload;
3. late supported-solid reuse check;
4. redundant post-reuse panel refresh; and
5. repeated effective-status signature scans.

The machine-readable
[performance-boundary register](contracts/phase1-performance-boundaries.json)
now completes the explicit-boundary branch of that requirement. It protects
the exact source and committed-report fingerprints, then classifies each
measurement as an operator action, nested component, harness enclosure,
same-process correctness observation or missing target boundary. Reconciliation
is performed within each run before medians are selected; independently
reported medians are never added or subtracted to manufacture a run total.

All five defects remain **not fixed**. The register instead states the only
safe current use and the evidence required by a later fix. In particular, the
complete enclosing panel/stage boundary may be used when declared, but the
prematurely persisted chair payload and unreconciled inner spans may not select
an optimisation. The warm solid result remains useful evidence that the panel
retains 94.70% of its comparable cold stage cost and that refresh/status work
dominates reuse; it is not permission to skip invalidation or physical-fit
validation.

Four target-architecture slots are deliberately present with status
`not-implemented-unmeasured`: lightweight routine edit without export,
explicit Validate/deferred exact geometry, export from already validated state,
and the reconciled complete edit-through-export journey. Phase 1 defines their
boundaries and legacy context without inventing values. The owning architecture
phases must populate them before the corresponding capability is optimised or
its legacy path is retired.

No current timing is accepted as a human-use budget. Routine editing,
explicit Validate/deferred reconstruction and complete edit-through-export
will continue to be measured separately under
[PERFORMANCE_SOP.md](PERFORMANCE_SOP.md); the current selected-export series
covers exact shapes already retained in the legacy fixture, while the
create-time series covers fresh legacy exact-shape construction only.

[PHASE1_SLICE_SCORECARD.md](PHASE1_SLICE_SCORECARD.md) now reconciles these
measurements with correctness and cut-boundary evidence. It deliberately does
not assign the transition calculation an invented saving: the recommendation
uses it to prove the Workbench's modular domain/façade path safely, while the
chair chain remains the high-payoff later performance target after accurate
core attribution, signature and provenance gates.

## Runtime and legacy-compatibility boundary

[`contracts/phase1-compatibility.json`](contracts/phase1-compatibility.json)
now separates three facts that must not be collapsed into a single claim:

1. the minimum Python feature floor used by standalone development code;
2. an exact FreeCAD host stack that has passed the current project evidence;
3. the versions and schemas of persisted input that a future migrator may
   accept.

The initial qualified and release-candidate profile is the current Linux
x86_64 stable `org.freecad.FreeCAD` Flatpak: FreeCAD 1.1.1 with its bundled
CPython 3.13.14, PySide6/Qt 6.10.3, OpenCASCADE 7.8.1 and Coin 4.0.8. The
repository's standalone CPython 3.12.3 environment establishes a 3.12.0
development floor for tools, tests and future domain imports. Users will not
be asked to install a separate Python beside FreeCAD. Windows, macOS, other
Linux packages/architectures and any other FreeCAD or bundled-library version
remain qualification-pending rather than being assumed compatible.

FreeCAD's official Addon schema defines `freecadmin`, optional `freecadmax`
and `pythonmin`. The intended initial manifest bounds are therefore
`1.1.1`, `1.1.1` and `3.12.0`, respectively. The real `package.xml` remains a
Phase 10 artifact and those values must be revalidated against the then-current
[official schema](https://github.com/FreeCAD/Addon-Manifest-Schema) and
[Addon template](https://github.com/FreeCAD/Addon-Template); this Phase 1
contract does not create a premature package.

The bounded legacy `.FCStd` ingress window is B14 and B15. A B15 action can
legitimately leave inherited B14 objects beside new or changed B15 objects, so
the exact mixed set is recognised. Pre-B14, versionless, unknown/future,
conflicting, corrupt or insufficiently parametric documents are
inspection-only or blocked: the Workbench must report them before a
transaction and must not mutate, migrate or export them. B14/B15 is the outer
window, not blanket family coverage. Phase 4 must provide a copied-target,
atomic migrator and a passing fixture for every entity family advertised for
release; one unqualified family blocks the whole Track Template write.

External configuration has a deliberately separate content-based window. The
current code accepts configuration schema 1, migrates schema 0 and a recognised
legacy saved-dialog shape, normalises last-input schemas 1/2/3, accepts preset
library schema 1 plus a legacy root array, and recognises two bounded preset
field aliases. Future, negative, malformed or otherwise unknown schemas fail
closed. None of those configuration migrations proves that an older `.FCStd`
is supported.

`tools/runtime_compatibility_probe.py` records only versions, platform class
and package identity. It qualifies the exact FreeCAD profile above and reports
field-level mismatches for drift. The contract validator also executes the
current B14 configuration, last-input and preset outer migrations from selected
AST definitions, checks every persisted schema anchor in both B14 and B15, and
mutates the contract to prove that unsupported broadening fails closed. No
successor document detector or migrator exists yet, and neither macro changed.

## Decision log

| Date | Decision | Status and reason |
| --- | --- | --- |
| 2026-07-19 | Use a standard-library AST inventory rather than importing the macro | Accepted for Phase 1 evidence; avoids launch/UI side effects and adds no runtime dependency |
| 2026-07-19 | Keep generated full inventory JSON out of Git | Accepted; the deterministic tool, source hashes, contract test and reviewed conclusions preserve the evidence without a large duplicate artifact |
| 2026-07-19 | Treat automated responsibility labels as provisional overlapping signals | Accepted; final ownership requires boundary and workflow review |
| 2026-07-19 | Add direct transition/station characterisation before selecting the slice | Accepted; representative, boundary, invalid-input and B14/B15 parity cases now protect the leading pure boundary |
| 2026-07-19 | Keep the Phase 0 fixture hash small and add a separate deep plain-line oracle | Accepted; it preserves the crossover baseline while characterising persistence, identity, production ordering and exact shapes without changing either macro; the `ordinary_track` implementation name remains a legacy evidence identifier |
| 2026-07-19 | Extend the plain-line oracle through one real handedness edit and two negative paths | Accepted; the copied-document recipe freezes mirrored semantics, save/reopen, zero-angle rejection, post-removal transaction abort and the separate last-used-input side effect without changing either macro |
| 2026-07-19 | Characterise the real explicit selected-export transaction before changing export architecture | Accepted; the copied-document recipe freezes all current formats/manifest, revision and overwrite semantics, parsed artifacts, atomic rollback and cleanup, and exposes repeated probe cost without changing either macro |
| 2026-07-19 | Characterise create-time production export independently from selected export | Accepted; the normal Generate recipe freezes successful production measures and persistence, measures the fixed end-to-end boundary, and deterministically bounds B14's partial-output/final-success-dialog defects without changing either macro or accepting them as future behaviour |
| 2026-07-19 | Use plain line/plain-line for track without S&C | Accepted; official UK railway usage replaces the project category “ordinary track”; B14/B15 and historical evidence identifiers remain unchanged, new APIs will use `plain_line`, and macro/component wording is separately gated in [TERMINOLOGY.md](TERMINOLOGY.md) |
| 2026-07-19 | Extend the fixed plain-line edit oracle through undo/redo and exact change-back | Accepted for Phase 1 evidence; every intermediate B14 state is frozen, but its three-entry geometry/schedule/report stack is a bounded legacy defect and the successor must make one accepted command one atomic undo unit |
| 2026-07-19 | Select the first extraction now | Deferred; transition solving leads on structural coupling, but workflow oracles, boundary contracts and representative profiles are not yet complete |
| 2026-07-20 | Use a source-informed procedural constituent pattern through a neutral project definition | Accepted; full-size definitions and named parts are canonical, Templot source/media is not canonical data, and FreeCAD B-reps may replace DXF `3DFACE` mechanics only under geometric oracle evidence; B15's five-box body remains legacy gap evidence |
| 2026-07-20 | Add reusable chair-definition packages and one assisted S1 assimilation pilot to RC scope | Accepted; scans/CAD/drawings/measurements fit the same definition used by native chairs, source evidence is not runtime truth, and arbitrary fully automatic conversion remains post-RC research |
| 2026-07-20 | Adopt explicit source/data/output licensing boundaries | Accepted; GPL source compliance is separated from engineering facts, Templot reference data/media and generated-output dependencies; neutral chair data and a one-way optional Templot adapter are required, CC0-1.0 is only a reviewed per-package target, and ordinary output receives no project NC restriction merely by generation |
| 2026-07-20 | Make the licensing boundary executable and scope the lineage audit | Implemented for owner review within the already accepted direction; rename the internal positive status to `project-cleared`, require a validated manifest before that status, record non-copyright reviews, add prospective DCO/data declarations, and split the audit into first-S1, core rail/timber, other S&C and legacy scopes so unresolved legacy breadth stays blocked without preventing independently evidenced S1 work |
| 2026-07-20 | Create the bounded first-S1/core rail-and-timber lineage register | Implemented for Phase 1 evidence; 16 current output-affecting groups have exact B14/B15 anchors, classifications, dispositions, evidence needs and owners, while the S1 and core scopes intentionally remain blocked pending independent evidence and accepted decisions |
| 2026-07-20 | Establish the bounded other-S&C and legacy B14/B15 lineage registers | Implemented for Phase 1 evidence; 24 grouped output dependencies have exact current anchors, statuses, owners and later gates, while 14 remain `reference-only`, 10 remain `unknown`, no output manifest exists and neither scope receives positive clearance |
| 2026-07-20 | Define a fail-closed exact-556b S1 oracle capture contract | Implemented for Phase 1 evidence and owner review; the exact source/member route, isolated settings, local-only artifact policy and DXF/STL semantics are executable, while the installed 5.55a candidate is rejected and the oracle remains visibly blocked pending an exact 556b executable, frozen fixture, capture and review |
| 2026-07-20 | Use B14's controlled connected pair as the first straight/station workflow oracle | Accepted for Phase 1 evidence; the copied-document recipe freezes route/station direction, stable identities, exact inherited joins, length editing, full history recovery, raw persistence and production catalogue without changing either macro; independent-datum GUI, physical station/platform and target-file export remain separate gaps |
| 2026-07-20 | Add a dedicated centreline-anchored standalone-turnout lifecycle oracle | Accepted for Phase 1 evidence; the copied-document recipe freezes one left/facing REA C10 creation, handed edit, exact history/persistence, stable objects, ordered production records, occupied-chainage rejection and in-transaction abort without changing either macro; trailing/straight/alternate hosts, integration, downstream stages and export remain separate gaps |
| 2026-07-20 | Record all five current candidate boundaries before selection | Implemented for Phase 1 evidence; the machine-readable register and fail-closed drift test freeze units, frames, tolerances, identities, ordering, schemas, effects and signature/invalidation behaviour without moving code, selecting a slice or clearing chair data |
| 2026-07-20 | Make an external FreeCAD Workbench distributed as an Addon the product target | Accepted by the project owner; the modular `tracktemplate` package is authoritative, Addon Manager installation is the intended release route, and the `.FCMacro` is limited to migration or explicit compatibility rather than a second implementation |
| 2026-07-20 | Score the five first-slice candidates using bounded static closure cuts and measured workflow evidence | Recommendation completed; schema 2 exposed root-versus-closure caller differences and the scorecard recommended the transition solver as a low-risk architecture pilot rather than a speed optimisation |
| 2026-07-20 | Select and freeze the transition-length architecture pilot | Accepted by the project owner; candidate-register schema 3 points to an exact fail-closed contract, `10.2A8A7B16` and `TrackTemplate.FCMacro` are reserved for the development composition path, B14/B15 remain unchanged and source movement has not started |
| 2026-07-20 | Define the initial runtime and legacy-document ingress window | Implemented for Phase 1 evidence and owner review; only the exact Linux x86_64 FreeCAD 1.1.1 Flatpak stack is currently qualified, standalone Python has a 3.12.0 floor, B14/B15 are the bounded future migration sources, unsupported hosts/documents fail closed, and Phase 4 still owns the copied-target migrator and family fixtures |
| 2026-07-21 | Reconcile the current performance evidence before using subprofiles | Implemented for Phase 1 evidence and owner review; nine controlled legacy profiles now have exact operator/nested/harness boundaries, all five instrumentation defects are explicitly bounded but not fixed, per-run reconciliation precedes medians, four target-pipeline slots remain visibly unmeasured and no observed timing is accepted as a budget or optimisation authority |
| 2026-07-21 | Add a focused automatic-crossover-timbering semantic and lifecycle oracle | Implemented for Phase 1 evidence and owner review; the copied fixture freezes the fixed `XO-001` records, calculation invalidation, reuse/history/persistence and clear path, while diagnostic persistence, display-only rebuild and incomplete abort cleanup are explicit defects rather than successor requirements and current timber data remains provenance-blocked |
| 2026-07-21 | Add a focused post-B4 chair-analysis persistence and reuse oracle | Implemented for Phase 1 evidence and owner review; the disposable fixed `XO-001` witness preserves 355 positions, 269 findings, semantic/display identities, reuse Undo/Redo and reopen, while premature timing persistence, full record extraction/metadata mutation on hits, repeated status scans and redundant panel refresh are bounded defects rather than successor requirements; current chair semantics remain provenance-blocked |
| 2026-07-21 | Classify fixed-XO chair-analysis invalidation and presentation controls | Implemented for Phase 1 evidence and owner review; all 23 settings, 11 emitted rail fields and 40 emitted timber fields are classified, representative mutations reproduce an actual stale result plus precision/order defects, and headless layer topology is bounded without treating visibility as GUI evidence or changing either macro |
| 2026-07-22 | Make reuse and maintainability explicit release invariants | Accepted by the project owner; each genuinely shared concept has one authoritative implementation behind a cohesive narrow tested interface, exploratory code is removed or promoted before retention, temporary duplication requires an owner/retirement gate, current structural/parity checks remain active and Phase 2 must add executable package import/dependency/cycle guards |
| 2026-07-22 | Track progress by evidenced exit conditions and outcome milestones | Accepted and implemented in `PROJECT_PLAN.md`; bars do not estimate time or effort, the initial Phase 1 register supported 6/9 evidenced conditions, nine value-based milestones connect the baseline to RC1 without weakening any phase gate, and `tests/validate_project_progress.py` prevents numerical drift without substituting for owner judgement |
| 2026-07-22 | Make release-critical workflow ownership finite and fail closed | Implemented for Phase 1 evidence and owner review; the canonical 14-row inventory is mirrored by one compact link registry with 12 bounded-executed and two defined-blocked oracle states, exact evidence/control paths, gap owners and future closure phases; this advances the Phase 1 dashboard to 7/9 without claiming that any open gap has passed |
| 2026-07-22 | Make the blocked first-S1 package/evidence plan reviewable | Implemented for Phase 1 evidence and owner review; `S1_PILOT_PLAN.md` records 15 accepted, recommended, owner-required and evidence-blocked decisions, recommends exact quantities/full-size millimetres/a declared chair frame/strict load failure, fixes intended uses and metric families, and explicitly prevents a working S1 name, conditional CC0 target or Templot comparison from becoming clearance |
| 2026-07-22 | Accept the blocked first-S1 package/evidence control | Accepted explicitly by the project owner; S1-04 through S1-06, the intended uses and conditional CC0 target are accepted as direction, while S1-07 through S1-15, the manifest, lineage, comparison oracle and production package remain blocked; this advances the Phase 1 dashboard to 8/9 without asserting chair geometry or clearance |
| 2026-07-22 | Make railway terminology uncertainty visible and fail closed | Implemented for Phase 1 closeout review; 13 bounded term families now use accepted, provisional, review-required or frozen-legacy states, six unresolved reviews have Phase 8/9 owners, exact B14/B15 phrases and 21 ordinary-named evidence paths are protected, and successor product surfaces reject known legacy tokens without claiming that lexical scanning proves semantic correctness |
| 2026-07-22 | Consolidate Phase 1 closeout evidence and decisions | Implemented for owner review; `PHASE1_CLOSEOUT.md` reconciles the nine gate conditions, exact runtime/ingress policy, 14 workflow gaps, five instrumentation defects, four unmeasured target slots, bounded legacy defects, blocked S1/provenance state, six terminology reviews, control/documentation staleness risk and the exact Phase 2 authority; Phase 1 remains 8/9 until explicit acceptance |
| 2026-07-22 | Accept and close Phase 1 | Accepted explicitly by the project owner, including P1-01 through P1-10; Phase 1 is 9/9 complete and only the bounded Phase 2 package/loading foundation is authorised, while every named workflow, GUI, performance, migration, provenance, S1, rights and terminology item remains mandatory at its later gate |

## Phase 1 closeout result and mandatory later gates

- Keep the 14-workflow coverage registry aligned with the canonical inventory;
  reopen its Phase 1 condition if a release-critical family lacks an owner,
  known oracle state or explicit gap.
- Preserve the accepted `S1_PILOT_PLAN.md` boundary: S1-07 through S1-15 and
  the actual package remain blocked under their named Phase 9 gates until
  evidence and the outstanding decisions exist.
- Preserve the accepted terminology-assurance control; its six open semantic
  reviews remain owned Phase 8/9 work rather than waived Phase 1 findings or
  silently normalised terminology.
- Preserve the exact `PHASE1_CLOSEOUT.md` acceptance boundary. Phase 2 may
  implement only the frozen transition-pilot package/façade/loading foundation
  and reserved small B16 composition root; calculation movement and caller
  routing begin only at Phase 3.
- Do not alter B14, B15, the selected contract or a later gate merely to ease
  foundation work.

### Scheduled later workflow gates

The workflow register makes these obligations finite and assigns them to the
phase that can actually implement and test them. They are not waived, but they
are not reasons to mutate immutable B14/B15 or hold Phase 1 open after its
inventory and decision gates pass:

- Phases 5 and 9 own corrected chair signature cones, upstream record
  extraction, turnout/plain-line/wider-crossover cases, lightweight real-GUI
  selection/history, B15 support/layout/solid invalidation and removal of the
  bounded timing, mutation and exact-Part presentation defects.
- Phases 6 to 8 own deferred Validate reconstruction; broader curve,
  spacing/easement, straight, turnout and crossover inputs; cancellation and
  export scopes; crossover preflight agreement; wider automatic timbering;
  real-GUI lifecycle evidence; and atomic successor recovery.
- Phase 7 must define the point-record/vector adapter before migrating the
  station family. Phase 9 must resolve the chair predicate/signature rules
  before moving that family. Neither changes the already selected Phase 2
  transition pilot.
- Each advertised output keeps its lineage and dependency manifest blocked
  until its field-level evidence, non-copyright reviews and strict
  `project-cleared` gate pass. The exact local Templot 556b capture remains a
  Phase 9 comparison-oracle input when the required executable and acquisition
  evidence become available; 5.55a and the B15 box body remain invalid
  substitutes.
- The four target-architecture performance slots are populated only when their
  lightweight edit, explicit Validate and exporter implementations exist.
  Phase 4 owns copied-target B14/B15 migration fixtures, and Phase 10 owns final
  Addon metadata and broader platform qualification.

Phase 1 closed on 2026-07-22 after all nine exit criteria in
[PROJECT_PLAN.md](PROJECT_PLAN.md) were evidenced and explicitly accepted.
