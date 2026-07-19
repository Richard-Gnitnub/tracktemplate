# Validation Strategy

## Purpose

Validation protects railway correctness while the macro is optimised and separated into architectural layers. Tests must distinguish analytical correctness, FreeCAD integration, display behaviour and production output.

## Current version roles

- `AdvancedTurnout.FCMacro` is the B14 baseline (`10.2A8A7B14`).
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro` is the B15 candidate (`10.2A8A7B15`).
- `tests/validate_b15.py` validates B15 structure/analysis and compares selected functions against B14.
- `tests/freecad_validate_b15.py` exercises the B15 chair display path in real headless FreeCAD.

These roles are current project state, not a permanent versioning scheme. Update this document when the baseline/candidate relationship changes.

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

The command is successful only when it exits with status zero **and** prints `B15 FreeCAD 1.1 headless smoke test passed`. FreeCADCmd loads command-line scripts under their filename stem rather than `__main__`; the test has an explicit runner for that execution mode.

The existing automated coverage does not validate every B14/B15 workflow. Select checks by the changed scope and report uncovered paths.

## Change matrix

| Change scope | Minimum validation |
| --- | --- |
| Documentation only | Links, paths, Markdown integrity and diff review |
| Pure analytical calculation | Syntax plus focused analytical/structural tests |
| Cache/signature logic | Cold calculation, valid reuse and invalidation cases |
| FreeCAD object or persistence | Headless FreeCAD plus save/reopen and cleanup checks |
| GUI display/editing | Headless checks plus real GUI exercise |
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

## Future validation assets

Before retiring a legacy path, add representative, non-sensitive fixtures or deterministic input recipes covering:

- curve/easement and multi-track generation;
- turnout creation and editing;
- straight- and curved-host crossovers;
- automatic timbering and chair analysis;
- lightweight preview selection/editing;
- exact validation and each production export family;
- failure rollback and document reopen.
