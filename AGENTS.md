# Project guidance

## Purpose and priorities

- This repository develops a FreeCAD macro for parametric model-railway track templates, including curves, straights, REA C10 turnouts and crossovers, timbering, chairs, host integration, and production exports.
- Correct railway geometry and production data take priority over speed. Unless the user explicitly requests a behaviour change, treat performance work as behaviour-preserving.
- Do not start a refactor from intuition alone. Inspect the relevant implementation and capture a repeatable baseline before editing.

## Architecture

- `reference/PROJECT_PLAN.md` is the canonical delivery sequence from the current checkpoint to a release candidate. Read it before starting source work, report work against its current phase, and do not claim a phase transition without its exit evidence and user acceptance.
- `reference/ARCHITECTURE.md` is the canonical strategic architecture. Read it before changing model boundaries, persistence, display construction, validation, export, or source organisation.
- `reference/MODULARISATION_PLAN.md` defines source boundaries, dependency direction and extraction gates. Read it before moving code or creating modules.
- The authoritative state is the parametric railway model: configuration, stable identities, topology, analytical results and production intent.
- SVG, Coin nodes and other viewport geometry are derived views, never an independent source of railway truth.
- Normal editing should use lightweight aggregated 2D presentation. Build exact `Part` shapes and solids only at an explicit Validate/Export boundary or when the user explicitly requests retained production geometry.
- The specific lightweight renderer remains an open design decision until a measured prototype proves editing, selection, persistence and performance.
- Migrate incrementally behind equivalence checks. Do not attempt a whole-macro rewrite or remove a legacy path before parity evidence and user acceptance.
- Follow `reference/PERFORMANCE_SOP.md` for measurement and `reference/VALIDATION.md` for the applicable validation matrix.

## Project phase discipline

- The current delivery phase is recorded in `reference/PROJECT_PLAN.md`; Phase 0 closed on 2026-07-19 and Phase 1 is current until its inventory exit gate is explicitly accepted.
- Keep phase work gate-based rather than inventing calendar promises before dependency and performance evidence exists.
- Bounded read-only investigation or disposable prototypes may reduce later risk, but they do not advance the phase or authorise production dependencies on an unaccepted decision.
- Record exact source state, validation, GUI evidence, performance evidence where applicable, decisions, exceptions and open risks at every phase close.
- Triage new features against the agreed release-candidate scope. Do not silently expand a migration change or its acceptance gate.

## Repository map

- `AdvancedTurnout.FCMacro` is the immutable B14 legacy comparison oracle (`10.2A8A7B14`) and contains the operator-facing turnout/crossover workflow benchmark. Its “Whole workflow” label does not yet mean the complete curve-to-export product pipeline.
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro` is the accepted B15 behavioural reference entering Phase 1 (`10.2A8A7B15`).
- `tests/validate_b15.py` provides fast structural and analytical checks for
  B15, compares selected railway functions, and enforces complete inherited
  B14-module AST parity after normalising the declared version, launch and
  recompute-instrumentation differences.
- `tests/freecad_validate_b15.py` is the real FreeCAD 1.1 headless smoke test for the B15 chair display layer.
- `tools/phase1_inventory.py` creates the deterministic read-only Phase 1 AST
  inventory without importing or executing either macro;
  `tests/validate_phase1_inventory.py` protects its alias, patch, caller and
  current-source contracts.
- `tests/validate_phase1_alignment.py` directly characterises the current
  transition-length and alignment-station boundary in B14 and B15 without
  importing FreeCAD; preserve its numerical, invalid-input and ordering oracles.
- `tools/freecad_bridge/ordinary_track_recipe.py` and
  `tests/validate_phase1_ordinary_track.py` own the separate Phase 1 deep
  semantic oracle for the fixed B14 ordinary curve/two-track document. Preserve
  its property types, normalized volatile fields, identities, ordering,
  production records and shape summaries; do not change the smaller Phase 0
  fixture hash to absorb this contract.
- `tools/freecad_bridge/ordinary_track_edit_recipe.py`,
  `tools/freecad_bridge/run-b14-ordinary-edit` and
  `tests/validate_phase1_ordinary_edit.py` own the bounded B14 ordinary-track
  handedness, save/reopen, invalid-input and transaction-abort oracle. Preserve
  the separate three-decimal dialog and exact solved persistence contracts, the
  frozen right-hand semantic hash, exact mirrored shape contract, and
  preference-store restoration.
- `tools/freecad_bridge/ordinary_track_export_recipe.py`,
  `tools/freecad_bridge/run-b14-ordinary-export` and
  `tests/validate_phase1_ordinary_export.py` own the bounded B14 explicit
  selected-export oracle. Preserve its exact 14-file names, 15-row manifest,
  frozen logical export hash, base/revision/overwrite equivalence, real
  mid-commit rollback, parsed output metrics and source/document cleanup
  contracts. Do not treat it as coverage of create-time export or deferred
  exact-shape construction.
- `reference/PHASE1_INVENTORY.md` owns the in-progress workflow, dependency,
  side-effect, candidate-slice and decision inventory. Update it as Phase 1
  evidence closes; its provisional static labels are not final module
  ownership.
- `reference/BASELINE.md` records the closed Phase 0 source fingerprints, environment, validation evidence, exclusions, decisions and gate evidence.
- `reference/benchmarks/` stores committed, non-sensitive raw benchmark reports plus clearly separated derived analysis. Preserve supplied readouts verbatim and state missing recipe/cache information.
- `tools/freecad_bridge/` is an optional development-only controller for isolated FreeCAD GUI observation and benchmarks. It is not a macro runtime dependency; read its README and verify its ignored local prerequisites before use.
- `reference/PROJECT_PLAN.md`, `reference/ARCHITECTURE.md`, `reference/MODULARISATION_PLAN.md`, `reference/TESTING_POLICY.md`, `reference/PERFORMANCE_SOP.md`, `reference/VALIDATION.md` and `reference/PROVENANCE.md` are maintained project guidance. Update the owning document when an accepted phase, decision, procedure, licence/provenance status or version role changes.
- `reference/t5_files_556b_06_feb_2025.zip` is source evidence. Treat it as read-only unless the user explicitly requests a change.
- `LICENSE` and `NOTICE.md` apply GPL-3.0-or-later to the project, preserve the Templot5 source-basis attribution, and record particular thanks to Martin Wynne and Steve Cornford. Preserve both files and all applicable upstream notices.
- `main.py` is PyCharm starter boilerplate, not the product entry point.
- Each macro launches through its final `run_macro()` call. Tests that load definitions deliberately remove only that final launch call.
- Version assignments occur in more than one compatibility layer. Change every applicable assignment together only when the user has approved a version change.

## Scope and change discipline

- Treat an explicitly mentioned macro as the target. If the target is ambiguous, confirm whether work belongs in the accepted B15 reference, the immutable B14 oracle, or both before editing. Never edit B14 merely to keep it aligned with B15.
- Make small, reviewable patches. Do not reformat or mechanically rewrite the complete multi-megabyte macro.
- Keep mechanical extraction separate from cleanup, optimisation and behaviour changes. Establish parity before improving moved code.
- Preserve UTF-8 encoding and compatibility with FreeCAD's bundled Python, `FreeCAD`, `Part`, `FreeCADGui`, and the existing PySide fallback.
- Do not add third-party runtime dependencies without approval.
- When consulting or adapting Templot5 material, preserve `reference/PROVENANCE.md`, the GPL-3.0-or-later project licence, and applicable upstream notices. Distinguish unprotected mathematical concepts, railway methods, functionality, and factual dimensions from potentially copyrightable code, comments, tables, selection, arrangement, or close translation; do not make unsupported clean-room or derivation claims.
- Do not silently change geometry, sampling, tolerances, topology gates, timber decisions, chair assignments, stable identities, ordering, metadata schemas, persistent property names, visibility, transaction/rollback behaviour, or exporter results.
- Do not weaken validation, remove required work, reduce geometric fidelity, or suppress diagnostics merely to improve a timing result.
- Preserve transactional behaviour: validate replacement geometry before committing document changes, and keep failure paths recoverable.
- Follow `reference/TESTING_POLICY.md`. Add proportionate automated evidence for every non-trivial new or changed behaviour; pure/domain functions normally require direct tests, while FreeCAD/GUI orchestration may be tested through a stable integration boundary.
- Do not change tests only to make an implementation pass. Change an existing oracle only with evidence that the test is wrong or the accepted requirement changed; explain why and obtain agreement on the new invariant.

## Performance work

- Follow `reference/PERFORMANCE_SOP.md`; do not invent a reduced benchmark procedure for an individual change.
- Use the B14 turnout/crossover **Whole workflow** report as the current operator-visible special-trackwork baseline and compare equivalent starting state, settings, stage sequence and cache state. Do not describe it as whole-product coverage.
- Measure both ordinary editing and deferred Validate/Export work so cost is not merely hidden at a later boundary.
- Preserve cache signatures and invalidation rules. A faster stale result is a correctness failure. Test both initial calculation and unchanged-result reuse when touching caches.
- Minimise redundant document recomputes, metadata writes, display-object creation, shape construction, and repeated traversals only when output equivalence is demonstrated.
- Keep FreeCAD object creation out of per-chair or similar hot loops where batching/compounds preserve the same result; the B15 structural test enforces this for the lightweight chair display.
- Do not introduce threads or processes around FreeCAD document or GUI operations without explicit approval and a dedicated correctness test.
- If a requested performance readout is visible only in FreeCAD, use the approved isolated development bridge when its local prerequisites are present. Otherwise ask for the copied report instead of inventing or estimating values.

## Verified validation commands

Run from the repository root. Use `reference/VALIDATION.md` to select additional checks for the changed scope.

Syntax-check both macros:

```bash
.venv/bin/python -c "import ast, pathlib; files=['AdvancedTurnout.FCMacro','model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8'), filename=f) for f in files]; print('Macro syntax checks passed')"
```

Run the fast B15 structural and analytical validation:

```bash
.venv/bin/python tests/validate_b15.py
```

Run the real FreeCAD 1.1 headless B15 smoke test:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD tests/freecad_validate_b15.py
```

Prepare the development-only FreeCAD bridge and its deterministic ignored B14
base fixture when they are absent:

```bash
tools/freecad_bridge/setup-freecad-cli
tools/freecad_bridge/build-b14-base
```

Both commands are reproducible from tracked inputs. The fixture builder refuses
to overwrite an existing FCStd or manifest.

Run the read-only Phase 1 ordinary-track document oracle on a copied fixture:

```bash
tools/freecad_bridge/run-b14-ordinary-snapshot \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base.FCStd
```

Run the Phase 1 ordinary-track edit and rollback oracle on a copied fixture:

```bash
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Run the Phase 1 ordinary-track selected-export oracle on a copied fixture:

```bash
tools/freecad_bridge/run-b14-ordinary-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

Run the controlled B14 crossover recipe in a fresh isolated FreeCAD process:

```bash
tools/freecad_bridge/run-b14-cold
```

Run the controlled unchanged-result series from a completed full cold document:

```bash
tools/freecad_bridge/run-b14-warm --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

Run the bounded B14-to-B15 real-GUI behavioural, reuse and persistence
acceptance from a completed controlled B14 cold document:

```bash
tools/freecad_bridge/run-b15-acceptance --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

Run the fast development-bridge recipe contract checks:

```bash
.venv/bin/python tests/validate_freecad_bridge.py
```

Run the deterministic Phase 1 macro-inventory contract checks:

```bash
.venv/bin/python tests/validate_phase1_inventory.py
```

Run the direct Phase 1 transition/station characterisation:

```bash
.venv/bin/python tests/validate_phase1_alignment.py
```

Run the fast Phase 1 ordinary-track oracle checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_track.py
```

Run the fast Phase 1 ordinary-track edit/rollback checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_edit.py
```

Run the fast Phase 1 ordinary-track selected-export checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_export.py
```

- These commands were verified with FreeCAD 1.1.1 in the current environment.
- A successful FreeCAD smoke run must print `B15 FreeCAD 1.1 headless smoke test passed`; an exit code without that sentinel is not evidence that FreeCAD executed the assertions.
- `tests/validate_b15.py` treats B14 as the immutable legacy oracle. If B14 is deliberately changed with explicit approval, do not automatically alter B15 or the comparison test merely to restore a pass; first determine the intended version scope and preserve the accepted checkpoint.
- Headless checks do not replace a real GUI workflow run. For geometry, document integration, display, export, or performance changes, run the exact target macro in FreeCAD and exercise the affected guided stages.
- Bridge runs must use the repository-local isolated profile and a copied/disposable document. Never attach the controller to an everyday FreeCAD session or an irreplaceable document, never approve an unexpected dialog, and confirm the exact bridge instance stopped after a snapshot, edit, export, cold, warm or acceptance run. Resolve recipe hosts by persisted centreline identity and place special trackwork by centreline chainage or a point projected to that centreline, not by UI ordering or an unanchored XYZ datum.
- Treat `benchmark-output/freecad-bridge/` as ignored raw evidence. Commit only sanitised reports with the exact recipe, hashes, cache/process state, validation outcome, limitations, and raw-artifact provenance.

## Completion and review

- Before reporting completion, inspect the diff for accidental broad changes and run every applicable check above.
- State which macro/version changed, which invariants were preserved, which tests ran, and any GUI validation still required.
- For project-plan work, state the current phase, which deliverables or gates changed, and whether the phase remains open or was accepted closed.
- For performance changes, include the before/after reports and identify any measurement noise or cache-state difference.
- Keep `.idea/`, `.venv/`, `__pycache__/`, generated FreeCAD documents, exported production files, and temporary benchmark artifacts out of commits.
- Do not commit or push unless the user asks.
