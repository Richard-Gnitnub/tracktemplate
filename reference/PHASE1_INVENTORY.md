# Phase 1 Product and Dependency Inventory

Status: **in progress; last updated 2026-07-20**. This document owns the Phase 1
inventory and concise decision log. It does not close Phase 1 or select the
first extraction slice.

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
| Inventory tool | `tools/phase1_inventory.py`, schema 1 |
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
| B14 role | Immutable legacy comparison oracle |
| B14 SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 role | Accepted behavioural reference |
| B15 SHA-256 | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| Chair source evidence | ignored Templot5 revision 556b SourceForge archive recorded in [PROVENANCE.md](PROVENANCE.md) |
| Chair source-audit date | 2026-07-20; read-only review of selected Pascal units |
| Source/data/output policy | explicitly accepted by the project owner on 2026-07-20; [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md) |
| Dependency/project-status manifest | `reference/schemas/dependency-manifest-v1.schema.json`, schema 1; enforced by `tools/validate_dependency_manifest.py` |
| First S1 pilot control manifest | structurally valid `unknown`; deliberately fails `--require-project-cleared` pending evidence, permissions, licence, non-copyright reviews and owner acceptance |
| Lineage audit scopes | first S1; core rail/timber used by S1; other S&C output; legacy B14/B15 output |
| First-S1/core lineage register | `reference/lineage/phase1-s1-core-lineage.json`, schema 1; 16 current output-affecting groups, all `reference-only` or `unknown`, with both scopes visibly `blocked` |
| First-S1/core lineage contract | `tests/validate_phase1_s1_lineage.py`; verifies register semantics, B14/B15 source anchors, the optional local archive hashes and the unresolved S1 manifest link |
| Current B14/B15 project-control output status | `unknown` pending its scoped output-affecting lineage audit; this is not a new output restriction |
| Production-source changes in this tranche | None |

The `ordinary_track` filenames, imports, commands and recipe IDs in this
inventory are frozen legacy evidence identifiers. Living prose follows
[TERMINOLOGY.md](TERMINOLOGY.md) and describes the subject as plain line.

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

Validate the executable dependency-manifest controls and the deliberately
unresolved S1 pilot record:

```bash
.venv/bin/python tests/validate_licensing_controls.py
.venv/bin/python tools/validate_dependency_manifest.py \
  reference/manifests/s1-chair-pilot.dependency-manifest.json
.venv/bin/python tests/validate_phase1_s1_lineage.py
```

Run the first direct B14/B15 transition and station characterisation oracle:

```bash
.venv/bin/python tests/validate_phase1_alignment.py
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

- `chairs_unit.pas` and `chairs_unit_x.pas` define separate `T_2d_data` and
  `T_3d_data` records. `init_2d_rea` and `init_3d_rea` populate full-size chair
  bases, corner radii, bolt centres, seat/plinth thicknesses, jaw sections,
  ribs, fillets, slopes, key and rail-fit/manufacturing parameters.
- `draw_chairs_on_timber` resolves chair families and placements, builds
  constituent jaw, seat and key records, and refers to reusable component
  blocks such as `S1OUTJAW`, `S1INJAW`, `S1SEAT` and `KEY`.
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
paths: nine are `reference-only` because their present basis includes Templot
reference data or source expression, and seven are `unknown` pending an
independent evidence source or an accepted engineering/manufacturing decision.
The register freezes 27 literal/function source anchors in B14/B15 and hashes
the six reviewed upstream units when the ignored local archive is available.
It also makes the C10 timber-stationing path an explicit legacy interface,
not a hidden dependency of a reusable S1 definition.
The upstream S1 comments point to “Standard Railway Equipment 1926”; as
recorded in [PROVENANCE.md](PROVENANCE.md), this is an unverified search lead,
not selected primary evidence.

Phase 1 still needs a reproducible S1 component/assembly oracle, accepted
primary evidence and agreed comparison metrics/tolerances. This audit records
structure, values, disposition and owners; it does not approve the current
values for a production package. No Templot code was copied into production,
no macro was changed and both registered scopes remain visibly `blocked`.

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

This is the initial owner/coverage map. “Gap” means the behaviour must be
characterised before its legacy path is moved; it does not imply the workflow
is known to be defective.

| Workflow family | Current oracle/evidence owner | Deterministic recipe or fixture | Principal Phase 1 gap |
| --- | --- | --- | --- |
| Curve/easement creation and editing | B15 reference; B14 oracle; direct transition/station characterisation; fixed create-result, edit-lifecycle, selected-export and create-time-export oracles | B14 default-base builder plus the four `run-b14-ordinary-*` characterisation wrappers | Fixed left/right replacement, undo/redo, exact change-back, persistence, negative paths and both export entry points for retained/fresh exact shapes are characterised; wider curve boundaries and future deferred Validate/reconstruction remain open; remaining curve functions lack direct oracles |
| Straight/stationing workflow | B15/B14 source plus direct calculation parity and the connected-pair lifecycle oracle | `run-b14-straight-station` creates and edits a deterministic entrance/exit pair from the fixed two-track curve | Connected route inputs, identities, inherited track order, travel-order stationing, joins/tangents, length editing, complete history recovery, raw persistence, exact document shapes and ordered production catalogue are characterised; the independent-datum GUI, physical station/platform, straight file export, straight-specific failures and wider configurations remain open |
| Multiple-track/spacing transition | Default B14 two-track base fixture plus deep create/edit/export document oracles | `build-b14-base` plus the four `run-b14-ordinary-*` characterisation wrappers | The fixed two-track configuration survives handedness replacement/reopen, selected export and create-time export; deferred Validate/reconstruction plus spacing/easement edit and invalid-input edge cases remain open |
| Standalone turnout | B15/B14 calculation parity plus B14's complete fixed-lifecycle semantic oracle | `run-b14-turnout` creates `TO-001` on persisted Main Track identity at chainage `746.298 mm`, edits its hand and exercises recovery | Curved-host left/facing creation, one handed edit, exact history/persistence, overlap rejection and injected transaction abort are characterised; trailing GUI orientation, straight/other hosts, wider inputs, removal/integration, downstream timber/chair stages and export remain open |
| Crossover geometry | B14 cold series and B15 acceptance report | Controlled `XO-001` bridge recipe | Preview/commit feasibility mismatch and curved-host coverage |
| Automatic timbering | Controlled `XO-001` workflow | Crossover cold recipe | Standalone turnout and plain-line timber decisions; focused failure/invalidation cases |
| Chair analysis and 2D presentation | B15 analytical tests and B14-to-B15 acceptance | Controlled completed `XO-001` document | Turnout/plain-line coverage, input-class invalidation, late timing payload and redundant refresh defects |
| Legacy approximate supported chair bodies | B15 smoke and acceptance | Completed `XO-001` acceptance path | Late reuse check, each solid-signature invalidation class and export-scope coverage; five-box S1/S1J bodies are gap evidence, not the final procedural chair oracle |
| Procedural chair definitions and exact components | Templot5 556b source audit, accepted architecture/licensing boundaries and the validated blocked first-S1/core lineage register | Current legacy inputs are reproducibly anchored; no exact constituent fixture yet | Frozen local Templot S1 comparison oracle, neutral package schema, rights-compatible primary evidence, accepted full-size values/transforms, package licence, comparison metrics and tolerances |
| Assisted chair assimilation | Accepted RC scope; no implementation oracle yet | One S1 pilot to be selected | Precise prototype designation, evidence provenance/rights, intended commercial/publication use, calibrated scan/CAD/measurement set, component landmarks, fit-residual policy, package licence and acceptance recipe |
| Host integration | Controlled crossover acceptance | `XO-001` stage 6 | Standalone turnout, removal/reversal, rollback and legacy-document variants |
| Save/reopen | B15 crossover acceptance and B14 plain-line edit-lifecycle oracle | Accepted B15 FCStd copy/reopen sequence plus `run-b14-ordinary-edit` | Broader entity families and future schema migration |
| SVG/DXF/STL/STEP and manifests | B14 source paths plus fixed plain-line selected- and create-time-export oracles | `run-b14-ordinary-export` covers revision/overwrite/atomic rollback; `run-b14-ordinary-create-export` covers the normal Generate entry point, all four formats, manifest, persistence and final-task failure | Cancellation, other scopes/entity families, accepted create-time all-files rollback, future deferred exact-shape reconstruction, other-S&C/legacy lineage maps and integration of the dependency/project-status manifest |
| Failure recovery | Transactional source paths, strict bridge dialog policy, plain-line edit lifecycle and both export fault injections | Edit oracle proves zero-angle rejection/post-removal abort and bounds B14's three-entry incomplete Undo states; selected export proves byte restoration; create-time export freezes the current 13-file partial result and unchanged document | Make successor edit commands and create-time output atomic under accepted contracts; add equivalent fixtures for other release-critical workflows |

Existing crossover evidence remains owned by
[benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md),
[benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md),
and
[benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md](benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md).
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

## Boundary-data inventory still required

The fixed plain-line, connected-straight and standalone-turnout oracles now
record the first concrete subsets: length/angle units, global document,
travel-order station and host-chainage frames, template-set/track/route/
turnout/record identities, exact join tolerances, object and production-record
ordering, persisted property/raw JSON schemas and volatile-field
normalisation. Before selecting the slice, Phase 1 must still record the exact
contract for every candidate rather than infer it from variable names:

- model and output units, including every degrees/radians and model/real-scale
  conversion;
- global XY, local alignment, turnout-local and host-chainage coordinate frames;
- geometric, station, topology, fit and export tolerances;
- stable entity, path, rail, timber, chair, production-record and document
  identities;
- chair-definition/package versions, constituent identities, exact source
  values and units, procedural profiles/cross-sections, local datums,
  rail-interface contracts, prototype/manufacturing separation, provenance,
  residual metrics and acceptance state;
- deterministic ordering rules and JSON/property/manifest schemas;
- complete analysis, support, layout, exact-solid and export signatures; and
- every relevant input class, cache reuse rule and invalidation/change-back
  case.

The static tool identifies where these values are used. It does not establish
their semantic contract.

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

No current timing is accepted as a human-use budget. Routine editing,
explicit Validate/deferred reconstruction and complete edit-through-export
will continue to be measured separately under
[PERFORMANCE_SOP.md](PERFORMANCE_SOP.md); the current selected-export series
covers exact shapes already retained in the legacy fixture, while the
create-time series covers fresh legacy exact-shape construction only.

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
| 2026-07-20 | Use B14's controlled connected pair as the first straight/station workflow oracle | Accepted for Phase 1 evidence; the copied-document recipe freezes route/station direction, stable identities, exact inherited joins, length editing, full history recovery, raw persistence and production catalogue without changing either macro; independent-datum GUI, physical station/platform and target-file export remain separate gaps |
| 2026-07-20 | Add a dedicated centreline-anchored standalone-turnout lifecycle oracle | Accepted for Phase 1 evidence; the copied-document recipe freezes one left/facing REA C10 creation, handed edit, exact history/persistence, stable objects, ordered production records, occupied-chainage rejection and in-transaction abort without changing either macro; trailing/straight/alternate hosts, integration, downstream stages and export remain separate gaps |

## Remaining Phase 1 work

- Complete operator workflow inputs, outputs, persisted properties, guided
  stages, failure and rollback maps for every row above.
- Extend the fixed curve/multiple-track recipe through broader boundary cases
  and explicit Validate/deferred reconstruction; extend straight coverage to
  the independent-datum GUI, physical station/platform, target-file export and
  straight-specific negative paths; cover
  cancellation and other export scopes, converge create-time output failure on
  an accepted atomic/UI contract, and extend the standalone-turnout fixture to
  trailing/straight/alternate-host inputs, removal/integration, downstream
  timber/chair stages and target-file export.
- Record candidate boundary schemas, units, frames, tolerances, identities,
  ordering, signatures and invalidation inputs.
- Keep the first-S1/core register blocked until its named evidence and decision
  gates are resolved; create bounded other-S&C and legacy B14/B15 registers
  with current statuses, owners and later gates. The machine-readable
  manifest, validator, non-copyright fields and contribution declaration now
  exist; wire their fail-closed `project-cleared` gate into the later
  package/export path.
- Complete the Templot chair-generation data-flow/value/transform map; produce
  or define the reproducible recipe for a frozen S1 constituent/assembly oracle
  and record any unavailable evidence without substituting the B15 box body.
- Specify the versioned chair-definition package and assisted-assimilation
  boundary, including provenance and corrupt/unsupported-package behaviour;
  confirm the pilot's precise prototype designation, rights-compatible primary
  evidence, package licence, commercial/publication use, component landmarks,
  rail section, fit metrics and tolerances with the project owner.
- Reconcile instrumentation and profile the proposed lightweight routine
  editing path and complete Validate/Export path without double-counting or
  treating the current exact-shape replacement measurement as its budget.
- Decide the supported FreeCAD/Python baseline and proposed legacy-document
  support window.
- Score the final candidate slices using correctness coverage and measured
  resource cost as well as static coupling.
- Agree the first slice, legacy comparison path and exact acceptance evidence
  with the project owner.

Phase 1 remains open until all exit criteria in
[PROJECT_PLAN.md](PROJECT_PLAN.md) are met and accepted.
