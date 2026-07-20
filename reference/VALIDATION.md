# Validation Strategy

## Purpose

Validation protects railway correctness while the macro is optimised and
separated into architectural layers. Tests must distinguish analytical
correctness, FreeCAD integration, display behaviour and production output.
[TESTING_POLICY.md](TESTING_POLICY.md) defines the project-wide obligation to
add tests and the limited circumstances in which an existing test oracle may
change.

## Current version roles

- `AdvancedTurnout.FCMacro` is the immutable B14 legacy comparison oracle (`10.2A8A7B14`).
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro` is the accepted B15 behavioural reference entering Phase 1 (`10.2A8A7B15`).
- `tests/validate_b15.py` validates B15 structure/analysis, compares selected
  railway functions, and proves complete inherited-module AST parity with B14
  after normalising only version, launch, docstring, and recompute-instrumentation
  differences.
- `tests/freecad_validate_b15.py` exercises the B15 chair display path in real headless FreeCAD.

B15 passed the bounded real-GUI, reuse, solid-equivalence, and save/reopen
qualification recorded in
[benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md](benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md).
The project owner accepted that evidence and the formal version roles on
2026-07-19. Acceptance is bounded to the declared B15 delta; B14 remains
available as the immutable legacy oracle for every Phase 1 characterisation
slice and later parity check.

These roles are current project state, not a permanent versioning scheme. Update this document when the oracle/reference relationship changes.

## Validation layers

### 1. Source and structural validation

- Parse every changed macro as Python.
- Check version assignments and launch boundaries.
- Prevent accidental whole-file rewrites or unrelated changes.
- Verify required function, schema and workflow structure.

### 2. Analytical validation

- Exercise pure calculations without depending on a FreeCAD GUI.
- Compare geometry records, topology, timbers, chairs, findings, stable identities and deterministic ordering.
- Test cache misses, valid reuse and invalidation after every relevant input class changes.

### 3. FreeCAD document validation

- Run against the supported FreeCAD version.
- Verify object types, properties, grouping, visibility, transactions, recomputes and cleanup.
- Confirm save/reopen behaviour when persistence changes.
- Ensure transient validation/export objects do not leak into the editable document.

### 4. Presentation validation

- Exercise the affected view in the GUI.
- Check visual alignment, style layers, visibility, selection-to-domain identity mapping and edit handles.
- Verify parameter edits, undo/redo, document close/reopen and cache invalidation.
- Treat the preview as display evidence only, never exact production validation.

### 5. Exact geometry and export validation

- Compare legacy and replacement bounds, lengths, profiles, topology and solid validity.
- Verify scale and planarity for SVG/DXF outputs.
- Verify valid solids/meshes for STEP/STL outputs.
- Compare filenames, categories, record IDs and manifest rows deterministically.
- Exercise staging, overwrite handling, failure rollback and transient-object cleanup.
- For procedural chairs, compare named constituents, full-size dimensions,
  profiles/cross-sections, datums, rail interfaces, topology and assembled
  placement against the accepted reference. FreeCAD B-rep and Templot
  DXF/STL tessellations need not be byte- or face-order-identical when the
  agreed geometric oracle proves equivalence.

### 6. Chair-definition and assimilation validation

Chair work has an additional validation boundary because the accepted
production requirement deliberately exceeds the B15 five-box S1/S1J body.
B15 remains the behavioural reference for its declared analysis,
representation, persistence and cache delta; its rectangular body is gap
evidence, not the future exact chair oracle.

Before a chair definition or generator is accepted:

- parse and validate the definition without FreeCAD/Qt, then prove a
  deterministic serialise/load/serialise round-trip and stable definition and
  component identities;
- reject missing required units, frames, datums, components, provenance,
  package versions or rail-interface data, and reject unsupported future
  versions without partial geometry generation;
- prove prototype source values and geometry are separate from model scale,
  rail-fit policy and manufacturing compensation, with complete signatures and
  invalidation for each input class;
- generate every in-scope named constituent through the common procedural
  builder, assemble reusable prototypes by deterministic transforms, and
  regenerate without the source scan/CAD file or retained FreeCAD shapes;
- compare the native S1 definition with the frozen Templot component/assembly
  oracle using agreed dimensional, section/profile, surface-distance,
  interface, bounds, topology and solid-validity metrics;
- prove rail fit, clearances, keys or loose components and applicable
  fastening/plug interfaces independently of visual plausibility;
- verify lightweight 2D symbols remain derived from the same accepted
  definition and do not construct production solids during routine editing;
  and
- compare deterministic STL/STEP and any retained-component outputs after
  exact validation, including separate-part identities and assembly placement.

For the assisted S1 assimilation pilot, also validate calibration, units,
coordinate frame, operator-declared components/landmarks, measured versus
inferred values, unresolved findings, provenance/file hashes and the reported
regenerated-versus-source residuals. Acceptance requires recorded tolerances
and explicit operator approval. A low residual does not by itself validate
hidden, worn or nominal geometry.

Raw tessellation hash equality is not a general geometric oracle: meshing
settings and face ordering can change without changing the solid. Preserve
source hashes for provenance, then compare the regenerated geometry with
format-appropriate semantic metrics.

### 7. Performance validation

- Follow [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md).
- Report both editing cost and deferred Validate/Export cost.
- Prove that an optimisation did not achieve speed by changing results or validation scope.

## Verified commands

Run from the repository root.

Syntax-check both current macros:

```bash
.venv/bin/python -c "import ast, pathlib; files=['AdvancedTurnout.FCMacro','model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8'), filename=f) for f in files]; print('Macro syntax checks passed')"
```

Fast B15 structural and analytical validation:

```bash
.venv/bin/python tests/validate_b15.py
```

Real FreeCAD 1.1 headless B15 smoke test:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD tests/freecad_validate_b15.py
```

Fast development-bridge recipe contract checks:

```bash
.venv/bin/python tests/validate_freecad_bridge.py
```

Deterministic Phase 1 macro-inventory contract checks:

```bash
.venv/bin/python tests/validate_phase1_inventory.py
```

This validates the analyser against a synthetic shadowing/alias/patch fixture,
then checks the exact immutable B14 and accepted B15 source fingerprints and
their current structural/candidate facts. It does not execute either macro.

Phase 1 licensing-control and manifest-gate checks:

```bash
.venv/bin/python tests/validate_licensing_controls.py
.venv/bin/python tools/validate_dependency_manifest.py \
  reference/manifests/s1-chair-pilot.dependency-manifest.json
.venv/bin/python tests/validate_phase1_s1_lineage.py
.venv/bin/python tests/validate_templot_s1_oracle.py
```

The test checks the Draft 2020-12 schema vocabulary, package/output structural
rules, fail-closed `project-cleared` semantics, non-copyright-rights reviews,
contribution authority, duplicate identities and the current S1 control
record. The S1 record must validate truthfully as `unknown`; it is not expected
to pass the strict release gate yet.

The lineage test separately enforces the bounded first-S1/core register: both
scopes must remain blocked, every current Templot-dependent entry must remain
`reference-only`, unresolved evidence and owners must be present, and all
source anchors must match the immutable B14 and accepted B15 files. When the
ignored local Templot archive is present it also verifies the archive and six
reviewed member hashes; a clean checkout does not require that archive.

The oracle-contract test validates the blocked exact-556b capture
specification, local-only artifact rule, rejected-version guard and synthetic
DXF/STL semantics. When the ignored source ZIP is present it also verifies the
archive plus seven required members, the visible 556b revision evidence and
the four named S1 component routes. It does not require an executable or raw
Templot media in a clean checkout and does not claim that the frozen oracle has
been captured.

Local source and candidate probes are:

```bash
.venv/bin/python tools/templot_s1_oracle.py validate-spec
.venv/bin/python tools/templot_s1_oracle.py probe-source
.venv/bin/python tools/templot_s1_oracle.py \
  inspect-executable /path/to/templot_5.exe
```

`inspect-executable` returns exit status 2 for an MZ-signature executable
candidate that lacks the required exact-556b marker or matches the recorded
rejected 5.55a fingerprint.
Do not run an accepted candidate in an everyday profile. After an isolated
capture exists, validate its bounded format semantics with:

```bash
.venv/bin/python tools/templot_s1_oracle.py inspect-artifacts \
  --dxf benchmark-output/templot-s1-oracle/<capture>.dxf \
  --stl benchmark-output/templot-s1-oracle/<capture>.stl
```

This command reports a `semantically-valid-unaccepted-capture`; it verifies
named component blocks/inserts, direct assembly/base faces, ASCII STL
structure, hashes, counts and bounds. It cannot by itself prove source
revision, effective GUI settings, solid equivalence or acceptance.

Any package or output proposed for the positive internal status must
additionally pass:

```bash
.venv/bin/python tools/validate_dependency_manifest.py \
  --require-project-cleared path/to/dependency-manifest.json
```

Direct Phase 1 transition/station characterisation:

```bash
.venv/bin/python tests/validate_phase1_alignment.py
```

This extracts only the exact B14/B15 calculation definitions under test into
a standalone Python namespace. It asserts representative and boundary values,
invalid-input diagnostics, station clamping/interpolation/duplicate-point
ordering, and exact B14/B15 result equality without importing FreeCAD.

Fast Phase 1 plain-line document-oracle contract checks (the test and wrapper
retain legacy `ordinary` identifiers):

```bash
.venv/bin/python tests/validate_phase1_ordinary_track.py
```

This checks volatile-value normalisation, deterministic hashing, null and valid
shape summaries, the persisted property-schema reader, and the isolated runner
contract without importing FreeCAD. The bounded real-FreeCAD oracle is:

```bash
tools/freecad_bridge/run-b14-ordinary-snapshot \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base.FCStd
```

Repeat `--base` to compare independent serialisations. The runner operates only
on copies, closes them without saving, and requires the frozen deep semantic
hash covering the fixed plain-line curve/two-track document.

Fast Phase 1 plain-line edit lifecycle/rollback contract checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_edit.py
```

This protects the separate rounded dialog-input and exact persisted-input
contracts, left/right mirror comparison, frozen right-hand semantic hash,
source-level transaction ordering, complete-document history sequence,
undo/redo measurement boundaries, and isolated runner/fault-injection
structure without importing FreeCAD. Exercise the bounded real-GUI path with:

```bash
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command acts only on a copied document. It must prove a `+90°` to `-90°`
replacement changes only handedness fields and reflected Y bounds; validate
every semantic state across the exact three-entry Undo/Redo stack; prove an
explicit change-back exactly restores the initial document; recover the
right-hand document by undoing change-back; survive save/reopen with cleared
history; reject zero angle without document mutation; abort a deliberately
failed replacement transaction after generated-output removal; restore the
isolated preference store; and leave the source fixture byte-identical. The v2
controlled series and its bounded B14 atomicity defect are recorded in
[benchmarks/2026-07-19-b14-plain-line-edit-lifecycle-series.md](benchmarks/2026-07-19-b14-plain-line-edit-lifecycle-series.md).
The preceding v1 replacement/rollback evidence remains in
[benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md](benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md).

Fast Phase 1 plain-line export contract checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_export.py
```

This checks the frozen filenames, manifest schema, logical-output
normalisation, B14 source fingerprint, selected-export staging/commit/rollback,
create-time post-document-commit/per-file ordering and both isolated runner
structures without importing FreeCAD. Exercise the explicit selected-export
GUI/exporter path with:

```bash
tools/freecad_bridge/run-b14-ordinary-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command acts only on a copied document. It must create the exact 14-file
DXF/SVG/STL/STEP/CSV variant, preserve it while allocating `_Rev_02`, replace
a sentinel through confirmed atomic overwrite, and restore every destination
byte after an injected mid-commit failure. It also parses output bounds and
solid/mesh topology, requires the frozen logical export hash, leaves nine
document objects and no staging directory, and keeps the source and copied
FCStd byte-identical. The accepted three-run characterisation and limitations
are recorded in
[benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md](benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md).

Exercise production export inside B14's normal Generate action with:

```bash
tools/freecad_bridge/run-b14-ordinary-create-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The copied-document recipe must perform one successful replacement/export and
one deterministic final-task failure. It requires the frozen normalised
document and success-output hashes, parsed production metrics identical to the
selected-export oracle, exactly 13 tasks plus manifest, clean one-pass
preflight with only the expected output-directory information item, nine
objects, preference restoration and save/reopen persistence.
The diagnostic failure must retain the frozen 13-file partial directory and
one manifest failure row without leaking temporary objects/files. That result
documents B14; it is not the accepted transaction contract for a migrated
exporter. The controlled three-run evidence is recorded in
[benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md](benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md).

Fast Phase 1 connected-straight and stationing workflow checks:

```bash
.venv/bin/python tests/validate_phase1_straight_station.py
```

This extracts the exact B14/B15 straight construction, connection validation
and station functions without importing either macro. It proves B14/B15 AST
and result parity for the controlled pair, exact travel-order stationing and
joins, one independent reverse/right-side two-track datum, negative contract
checks, source-level pre-transaction ordering and the isolated runner
structure. Exercise the real copied-document GUI path with:

```bash
tools/freecad_bridge/run-b14-straight-station \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command must use B14's real pair control and normal Replace action; create
the deterministic `600/600 mm` entrance/exit pair; recover the exact base and
created states through all three Undo/Redo entries; edit to `750/450 mm` while
preserving exact curve geometry and stable route identities; recover both edit
states through Undo/Redo; and preserve raw Settings/Template JSON, 23 objects,
12 ordered production records and the frozen workflow hash across save/reopen.
It must restore isolated preferences and leave the source fixture byte-
identical. The controlled series is recorded in
[benchmarks/2026-07-20-b14-straight-station-workflow-series.md](benchmarks/2026-07-20-b14-straight-station-workflow-series.md).
This is alignment stationing evidence, not coverage of a physical
station/platform or straight target-file export.

Fast Phase 1 standalone-turnout workflow checks:

```bash
.venv/bin/python tests/validate_phase1_turnout.py
```

This extracts the exact B14/B15 REA C10 dimension, handing/orientation,
valid-toe, occupied-interval and edit-summary functions without importing
either macro. It proves AST/result parity for the fixed analytical contract,
invalid-input diagnostics, persisted host-identity selection, source-level
pre-transaction construction and commit/abort structure, frozen semantic
hashes and the isolated runner/fault-injection contract. Exercise the real
copied-document GUI path with:

```bash
tools/freecad_bridge/run-b14-turnout \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command must use B14's real turnout manager, resolve Main Track by
persisted identity, create left-hand/facing `TO-001` at chainage `746.298 mm`,
and change only its hand to right. It must preserve stable object names and
the exact inherited plain-line geometry; recover exact before/after semantics
through the single-entry creation and edit Undo/Redo cycles; reject an
occupied-chainage creation without mutation; abort an injected first-mutation
edit failure; and preserve the frozen 17-object, 10-record right-hand state
across save/reopen. It must leave the source fixture byte-identical and retain
top-view, manager and full-window evidence. The controlled series is recorded
in
[benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md](benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md).
This is one B14 legacy comparison oracle, not canonical turnout data or
coverage of trailing/straight/alternate hosts, downstream timber/chair stages
or target-file export.

Fresh-checkout development-bridge and deterministic B14 fixture setup:

```bash
tools/freecad_bridge/setup-freecad-cli
tools/freecad_bridge/build-b14-base
```

The fixture command refuses to overwrite existing output. A bounded bridge
lifecycle check may then run `tools/freecad_bridge/run-b14-cold --stages
geometry`.

The controlled representative performance sequence is:

```bash
tools/freecad_bridge/run-b14-cold
tools/freecad_bridge/run-b14-warm --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

The warm command accepts only a completed seven-stage cold document with its
sibling `run.json`. It performs one warm-up and exactly three measured
unchanged-result iterations, and fails if object, cache-signature, chair-count,
or solid-shape identity changes. These long-running GUI benchmarks are
checkpoint/performance evidence, not part of the fast edit loop.

Run the bounded B14-to-B15 behavioural acceptance from a completed controlled
B14 cold document with:

```bash
tools/freecad_bridge/run-b15-acceptance \
  --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

This long-running GUI check verifies the exact inherited analysis/support and
non-chair leaf geometry, the B15 layout representation and unchanged-result
reuse, controlled removal of retained B14 solids, fresh B15 solid construction,
solid reuse/equivalence, effective status, save/reopen persistence, rendered
manager/view evidence, and non-mutation of the input document. Its timings are
observations only and are not approved interactive budgets.

The FreeCADCmd B15 command is successful only when it exits with status zero
**and** prints `B15 FreeCAD 1.1 headless smoke test passed`. FreeCADCmd loads
command-line scripts under their filename stem rather than `__main__`; the test
has an explicit runner for that execution mode.

The existing automated coverage does not validate every B14/B15 workflow. Select checks by the changed scope and report uncovered paths.

## Change matrix

| Change scope | Minimum validation |
| --- | --- |
| Documentation only | Links, paths, Markdown integrity and diff review |
| Pure analytical calculation | Syntax plus focused analytical/structural tests |
| Cache/signature logic | Cold calculation, valid reuse and invalidation cases |
| FreeCAD object or persistence | Headless FreeCAD plus save/reopen and cleanup checks |
| GUI display/editing | Headless checks plus real GUI exercise |
| Development bridge or benchmark recipe | Fast bridge contract checks plus a bounded isolated GUI lifecycle run |
| Railway geometry/topology/timber/chair rules | Representative analytical comparisons and real workflow validation |
| Export or exact geometry | Target-format output, manifest, rollback and deterministic repeat checks |
| Chair-definition schema or package loader | Standalone schema validation, deterministic round-trip, corrupt/unsupported rejection, stable component IDs and provenance checks |
| Procedural chair generator | Templot/reference constituent and assembly comparison, rail-fit/interface checks, valid B-reps/exports, deterministic regeneration and no routine-edit solids |
| Assisted chair assimilation | Calibrated source fixture, landmark/component decisions, measured/inferred audit, residual metrics, unresolved findings, provenance and explicit acceptance |
| Architecture migration | Legacy/new parity, editing cost and complete Validate/Export cost |

## Manual GUI checklist

For an affected workflow:

1. Start from the documented representative state.
2. Run the exact target macro and confirm its version.
3. Exercise the changed guided stages.
4. Confirm view alignment, visibility and selection behaviour.
5. Make a parameter edit and verify the intended layers become dirty and regenerate.
6. Test undo/redo when the change affects editable document state.
7. Run explicit production validation.
8. Export each affected format to a temporary location.
9. Inspect summary/manifest diagnostics and confirm no transient objects remain.
10. Copy the performance report when the change has a resource objective.

## Failure policy

- Do not weaken an assertion solely because a refactor fails it.
- Determine whether the failure exposes a defect, an intentionally changed invariant or an obsolete test boundary.
- Obtain agreement before changing an accepted railway or production invariant.
- Record any check that could not be run and the risk it leaves.

## Observed regression obligations

The controlled B14 runs and export source/transaction audits expose six
behaviours that need focused tests with their eventual production fixes.
Do not encode the current defect as the expected result merely to increase the
test count.

1. Crossover preview/commit feasibility: use the same persisted host-centreline
   identities and Host A chainage for preview and transactional commit. Assert
   that the complete minimum-radius rule covers both mapped turnout roads and
   the connector, that a lower invalid chainage is rejected before document
   mutation, and that the documented valid chainage is accepted.
2. Chair timing persistence: run chair analysis, save, close and reopen the
   document, then assert persisted `performance_timings_ms` includes metadata
   updates, diagnostic display construction, document recompute, transaction
   commit and total duration, and reconciles with the enclosing stage boundary.
3. Effective-status reuse: query chair/support/layout/solid status through one
   shared snapshot or demonstrably bounded signature reuse, assert unchanged
   results are equivalent, then mutate each relevant input class and verify
   correct invalidation.
4. Supported-solid cache boundary and panel refresh: assert an unchanged valid
   solid returns before rebuilding its plan/fit inputs, retains exact object and
   shape identity, and does not trigger redundant parent/panel reconstruction or
   document recompute. Then change every solid-signature input class and prove
   that physical-fit validation and shape generation run again.
5. Create-time export transaction and final UI: the deterministic final-task
   oracle now proves B14's post-document-commit `run_macro()` path retains
   twelve task files plus its manifest when the final STEP fails, while the
   later overall dialog still says the outputs were created successfully.
   Preserve that diagnostic evidence, but converge the production path on an
   accepted all-files staging, manifest, rollback, cleanup and truthful-summary
   contract before this path is migrated.
6. Plain-line edit command atomicity: B14 records geometry replacement,
   production-schedule refresh and material-report refresh as three undo
   transactions, exposing observable but incomplete seven- and eight-object
   states. Preserve the lifecycle evidence, but require one
   accepted application command to create one complete undo unit and test the
   exact document after one Undo and one Redo.

## Future validation assets

Before retiring a legacy path, add representative, non-sensitive fixtures or deterministic input recipes covering:

- curve/easement and multi-track generation;
- turnout creation and editing;
- straight- and curved-host crossovers;
- automatic timbering and chair analysis;
- an exact local capture produced under the tracked frozen-Templot-S1
  constituent/assembly recipe (the recipe/validator exists; the exact 556b
  executable, fixture and artifacts remain blocked);
- a versioned native S1 chair-definition package with invalid/corrupt fixtures;
- one non-sensitive, project-cleared calibrated scan/CAD/measurement fixture for
  the assisted S1 assimilation pilot;
- lightweight preview selection/editing;
- exact validation and each production export family;
- failure rollback and document reopen.
