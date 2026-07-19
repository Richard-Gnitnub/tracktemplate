# Phase 1 Product and Dependency Inventory

Status: **in progress**. This document owns the Phase 1 inventory and concise
decision log. It does not close Phase 1 or select the first extraction slice.

## Purpose

Phase 1 chooses migration order from evidence. This first tranche records a
reproducible static view of the accepted B15 behavioural reference and the B14
legacy oracle, identifies order-sensitive implementation mechanisms, compares
the leading calculation candidates, and makes the remaining workflow,
correctness, boundary-data and performance work explicit.

The applicable gates are in [PROJECT_PLAN.md](PROJECT_PLAN.md), and source
movement remains governed by [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md).

## Evidence state

| Item | Value |
| --- | --- |
| Inventory date | 2026-07-19 |
| Inventory tool | `tools/phase1_inventory.py`, schema 1 |
| Ordinary-track oracle | `tools/freecad_bridge/ordinary_track_recipe.py`, schema 1 |
| Ordinary-track semantic SHA-256 | `b5641d79ff1fd77956f3ade8372da2f5b0dd50b6d42945aa611207242278b656` |
| B14 role | Immutable legacy comparison oracle |
| B14 SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 role | Accepted behavioural reference |
| B15 SHA-256 | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| Production-source changes in this tranche | None |

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

Run the first direct B14/B15 transition and station characterisation oracle:

```bash
.venv/bin/python tests/validate_phase1_alignment.py
```

Run the fast contract checks for the deeper B14 ordinary-track document oracle:

```bash
.venv/bin/python tests/validate_phase1_ordinary_track.py
```

Capture the real FreeCAD oracle from one or more copied fixtures with:

```bash
tools/freecad_bridge/run-b14-ordinary-snapshot \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base.FCStd
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
reverse caller neighbourhood. Counts describe static top-level definition
occurrences, not runtime invocation frequency.

| Candidate | Roots | Dependency definitions / lines | Direct callers | Caller closure | Platform signal | Duplicate names in closure | Existing position |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| Curve/easement/station family | 3 | 6 / 154 | 35 | 114 | FreeCAD via station interpolation | 0 | Strategically broad, too aggregated for a first move |
| Transition-length solver | 1 | 3 / 107 | 1 | 2 | None | 0 | Lowest structural coupling; initial representative/boundary oracle now present |
| Alignment station index | 1 | 1 / 25 | 15 | 77 | None directly | 0 | Pure-looking and foundational, but high fan-out and FreeCAD-derived point inputs |
| Alignment station interpolation | 1 | 2 / 22 | 30 | 107 | Direct `App.Vector` construction | 0 | Requires an explicit coordinate-record/adapter seam |
| Chair-analysis core | 4 | 39 / 1,396 | 18 | 57 | None in the bounded calculation closure | 9 | Best current tests, but substantial alias/schema coupling |

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
mutable-global, duplicate-definition or captured-alias signal. Its one direct
caller is `prepare_track_alignment`. The direct characterisation now locks the
default two-track outside solution, an inside solution, monotonic targets,
endpoint behaviour, invalid radius/range diagnostics and exact B14/B15 equality.
This is the current lowest-risk candidate for proving extraction mechanics, but
Phase 1 has not yet established its complete caller, editing and
Validate/Export workflow evidence, so it is not selected.

### Station maps

`alignment_station_data` is a single 25-line function with fifteen immediate
callers. It builds cumulative station data from point objects without directly
importing FreeCAD. `interpolate_alignment_station` is only 20 lines, but calls
`vector_xy`, which constructs `App.Vector`. This is a concrete boundary seam:
station arithmetic can be domain logic only when its point representation,
units, frame and adapter conversion are explicit.

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
However, nine names in that closure are repeated, and the active validator
calls `_A8A7A1_VALIDATE_CHAIR_POSITIONS`. The four-deep caller map reaches
analysis metadata, displays, physical support, exact chair solids, UI classes,
guided workflows and B15 cache wrappers. Characterisation must therefore lock
down record schemas, ordering, findings, aliases, signatures and invalidation
before movement.

## Release-critical workflow coverage inventory

This is the initial owner/coverage map. “Gap” means the behaviour must be
characterised before its legacy path is moved; it does not imply the workflow
is known to be defective.

| Workflow family | Current oracle/evidence owner | Deterministic recipe or fixture | Principal Phase 1 gap |
| --- | --- | --- | --- |
| Curve/easement creation and editing | B15 reference; B14 oracle; direct transition/station characterisation and fixed create-result document oracle | B14 default-base builder plus `run-b14-ordinary-snapshot` | Fixed create result is characterised; edit/reverse, failure/rollback, warm profile and export-through profile remain open; remaining curve functions lack direct oracles |
| Straight/station workflow | B15/B14 source only | None dedicated | Inputs, station semantics, edit behaviour, persistence and production output are uncharacterised |
| Multiple-track/spacing transition | Default B14 two-track base fixture and deep document oracle | `build-b14-base` plus `run-b14-ordinary-snapshot` | Default persisted result/production catalogue is characterised; edit, Validate/Export, invalid inputs and spacing/easement edge cases remain open |
| Standalone turnout | B15/B14 source and inherited parity checks | None dedicated | Creation/editing, handedness/orientation, straight/curved host, rollback and performance recipes |
| Crossover geometry | B14 cold series and B15 acceptance report | Controlled `XO-001` bridge recipe | Preview/commit feasibility mismatch and curved-host coverage |
| Automatic timbering | Controlled `XO-001` workflow | Crossover cold recipe | Standalone turnout and ordinary-track timber decisions; focused failure/invalidation cases |
| Chair analysis and 2D presentation | B15 analytical tests and B14-to-B15 acceptance | Controlled completed `XO-001` document | Turnout/ordinary track coverage, input-class invalidation, late timing payload and redundant refresh defects |
| Optional supported chair solids | B15 smoke and acceptance | Completed `XO-001` acceptance path | Late reuse check, each solid-signature invalidation class and export-scope coverage |
| Host integration | Controlled crossover acceptance | `XO-001` stage 6 | Standalone turnout, removal/reversal, rollback and legacy-document variants |
| Save/reopen | B15 crossover acceptance | Accepted B15 FCStd copy/reopen sequence | Parameter editing, undo/redo, change-back and broader entity families |
| SVG/DXF/STL/STEP and manifests | Source preflight/export paths | None end-to-end in the controlled pipeline | Deterministic target artifacts, bounds/scale, overwrite, rollback, cancellation and cleanup |
| Failure recovery | Transactional source paths and strict bridge dialog policy | Partial negative bridge assertions | Release-critical failure fixtures and proof of unchanged document/output state |

Existing crossover evidence remains owned by
[benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md),
[benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md),
and
[benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md](benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md).

## Fixed ordinary-track document contract

The Phase 0 fixture hash remains unchanged and intentionally small because it
is the crossover-recipe precondition. Phase 1 adds a separate deeper oracle.
In one isolated FreeCAD 1.1.1 run, the original 641,206-byte fixture and the
independently regenerated 636,344-byte fixture had distinct binary SHA-256
values but the same base semantic hash and the same deep semantic SHA-256
`b5641d79ff1fd77956f3ade8372da2f5b0dd50b6d42945aa611207242278b656`.

The deep contract establishes:

- nine named objects and exact group membership, with `SET-001` as the shared
  template-set identity and track numbers 1 and 2 as the ordinary centreline
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
It does not yet characterise parameter editing, reverse/right-hand generation,
undo/redo, failure rollback, export artifacts or interaction time.

## Boundary-data inventory still required

The fixed ordinary-track oracle now records the first concrete subset: its
length/angle property units, global document frame, template-set/track/record
identities, object and production-record ordering, persisted property/JSON
schema, and volatile-field normalisation. Before selecting the slice, Phase 1
must still record the exact contract for every candidate rather than infer it
from variable names:

- model and output units, including every degrees/radians and model/real-scale
  conversion;
- global XY, local alignment, turnout-local and host-chainage coordinate frames;
- geometric, station, topology, fit and export tolerances;
- stable entity, path, rail, timber, chair, production-record and document
  identities;
- deterministic ordering rules and JSON/property/manifest schemas;
- complete analysis, support, layout, exact-solid and export signatures; and
- every relevant input class, cache reuse rule and invalidation/change-back
  case.

The static tool identifies where these values are used. It does not establish
their semantic contract.

## Performance inventory status

The controlled crossover cold/warm series identifies genuine dominant costs,
but Phase 1 still lacks a reconciled curve-to-export product-pipeline profile.
Before profiles select an optimisation, the defects already recorded in
[VALIDATION.md](VALIDATION.md) must be closed or bounded:

1. geometry external/internal timing boundary gap;
2. prematurely persisted chair timing payload;
3. late supported-solid reuse check;
4. redundant post-reuse panel refresh; and
5. repeated effective-status signature scans.

No current timing is accepted as a human-use budget. Ordinary editing and
edit-through-Validate/Export will be measured separately under
[PERFORMANCE_SOP.md](PERFORMANCE_SOP.md).

## Decision log

| Date | Decision | Status and reason |
| --- | --- | --- |
| 2026-07-19 | Use a standard-library AST inventory rather than importing the macro | Accepted for Phase 1 evidence; avoids launch/UI side effects and adds no runtime dependency |
| 2026-07-19 | Keep generated full inventory JSON out of Git | Accepted; the deterministic tool, source hashes, contract test and reviewed conclusions preserve the evidence without a large duplicate artifact |
| 2026-07-19 | Treat automated responsibility labels as provisional overlapping signals | Accepted; final ownership requires boundary and workflow review |
| 2026-07-19 | Add direct transition/station characterisation before selecting the slice | Accepted; representative, boundary, invalid-input and B14/B15 parity cases now protect the leading pure boundary |
| 2026-07-19 | Keep the Phase 0 fixture hash small and add a separate deep ordinary-track oracle | Accepted; it preserves the crossover baseline while characterising persistence, identity, production ordering and exact shapes without changing either macro |
| 2026-07-19 | Select the first extraction now | Deferred; transition solving leads on structural coupling, but workflow oracles, boundary contracts and representative profiles are not yet complete |

## Remaining Phase 1 work

- Complete operator workflow inputs, outputs, persisted properties, guided
  stages, failure and rollback maps for every row above.
- Extend the fixed curve/multiple-track create-result recipe through editing,
  reversal, rollback, Validate and Export; create dedicated recipes or fixtures
  for station/straight, standalone turnout and end-to-end exports.
- Record candidate boundary schemas, units, frames, tolerances, identities,
  ordering, signatures and invalidation inputs.
- Reconcile instrumentation and profile the ordinary editing and complete
  Validate/Export paths without double-counting.
- Decide the supported FreeCAD/Python baseline and proposed legacy-document
  support window.
- Score the final candidate slices using correctness coverage and measured
  resource cost as well as static coupling.
- Agree the first slice, legacy comparison path and exact acceptance evidence
  with the project owner.

Phase 1 remains open until all exit criteria in
[PROJECT_PLAN.md](PROJECT_PLAN.md) are met and accepted.
