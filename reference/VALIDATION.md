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

### 6. Performance validation

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

Direct Phase 1 transition/station characterisation:

```bash
.venv/bin/python tests/validate_phase1_alignment.py
```

This extracts only the exact B14/B15 calculation definitions under test into
an ordinary-Python namespace. It asserts representative and boundary values,
invalid-input diagnostics, station clamping/interpolation/duplicate-point
ordering, and exact B14/B15 result equality without importing FreeCAD.

Fast Phase 1 ordinary-track document-oracle contract checks:

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
hash covering the fixed ordinary curve/two-track document.

Fast Phase 1 ordinary-track edit/rollback contract checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_edit.py
```

This protects the separate rounded dialog-input and exact persisted-input
contracts, left/right mirror comparison, frozen right-hand semantic hash,
source-level transaction ordering, and isolated runner/fault-injection
structure without importing FreeCAD. Exercise the bounded real-GUI path with:

```bash
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command acts only on a copied document. It must prove a `+90°` to `-90°`
replacement changes only handedness fields and reflected Y bounds, survive
save/reopen, reject zero angle without document mutation, abort a deliberately
failed replacement transaction after generated-output removal, survive a
second reopen, restore the isolated preference store, and leave the source
fixture byte-identical. The accepted three-run characterisation and exact
coverage boundary are recorded in
[benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md](benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md).

Fast Phase 1 ordinary-track selected-export contract checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_export.py
```

This checks the frozen filenames, manifest schema, logical-output
normalisation, B14 source fingerprint, selected-export staging/commit/rollback
source order and isolated runner structure without importing FreeCAD. Exercise
the real GUI/exporter path with:

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

The controlled B14 runs and the selected-export source/transaction audit expose
five behaviours that need focused tests with their eventual production fixes.
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
5. Create-time export transaction: B14's post-document-commit `run_macro()`
   path calls `run_production_export()`, commits successful output tasks one at
   a time and can retain them when a later task fails. Add a deterministic
   later-task failure oracle and converge it with an accepted all-files staging,
   manifest, rollback and cleanup contract before this path is migrated.

## Future validation assets

Before retiring a legacy path, add representative, non-sensitive fixtures or deterministic input recipes covering:

- curve/easement and multi-track generation;
- turnout creation and editing;
- straight- and curved-host crossovers;
- automatic timbering and chair analysis;
- lightweight preview selection/editing;
- exact validation and each production export family;
- failure rollback and document reopen.
