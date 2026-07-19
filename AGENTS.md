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

- The current delivery phase is recorded in `reference/PROJECT_PLAN.md`; Phase 0 is current until its checkpoint and baseline exit gate is explicitly closed.
- Keep phase work gate-based rather than inventing calendar promises before dependency and performance evidence exists.
- Bounded read-only investigation or disposable prototypes may reduce later risk, but they do not advance the phase or authorise production dependencies on an unaccepted decision.
- Record exact source state, validation, GUI evidence, performance evidence where applicable, decisions, exceptions and open risks at every phase close.
- Triage new features against the agreed release-candidate scope. Do not silently expand a migration change or its acceptance gate.

## Repository map

- `AdvancedTurnout.FCMacro` is the current B14 baseline (`10.2A8A7B14`) and the file containing the operator-facing whole-workflow benchmark.
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro` is the B15 candidate (`10.2A8A7B15`).
- `tests/validate_b15.py` provides fast structural and analytical checks for B15 and compares selected railway functions with the B14 baseline.
- `tests/freecad_validate_b15.py` is the real FreeCAD 1.1 headless smoke test for the B15 chair display layer.
- `reference/BASELINE.md` records the current Phase 0 source fingerprints, environment, validation evidence, exclusions and remaining gates.
- `reference/PROJECT_PLAN.md`, `reference/ARCHITECTURE.md`, `reference/MODULARISATION_PLAN.md`, `reference/PERFORMANCE_SOP.md` and `reference/VALIDATION.md` are maintained project guidance. Update the owning document when an accepted phase, decision, procedure or version role changes.
- `reference/t5_files_556b_06_feb_2025.zip` is source evidence. Treat it as read-only unless the user explicitly requests a change.
- `main.py` is PyCharm starter boilerplate, not the product entry point.
- Each macro launches through its final `run_macro()` call. Tests that load definitions deliberately remove only that final launch call.
- Version assignments occur in more than one compatibility layer. Change every applicable assignment together only when the user has approved a version change.

## Scope and change discipline

- Treat an explicitly mentioned macro as the target. If the target is ambiguous, confirm whether work belongs in the B14 baseline, the B15 candidate, or both before editing.
- Make small, reviewable patches. Do not reformat or mechanically rewrite the complete multi-megabyte macro.
- Keep mechanical extraction separate from cleanup, optimisation and behaviour changes. Establish parity before improving moved code.
- Preserve UTF-8 encoding and compatibility with FreeCAD's bundled Python, `FreeCAD`, `Part`, `FreeCADGui`, and the existing PySide fallback.
- Do not add third-party runtime dependencies without approval.
- Do not copy or translate code from the local Templot5 reference archive until project licensing, provenance and required attribution have been explicitly decided.
- Do not silently change geometry, sampling, tolerances, topology gates, timber decisions, chair assignments, stable identities, ordering, metadata schemas, persistent property names, visibility, transaction/rollback behaviour, or exporter results.
- Do not weaken validation, remove required work, reduce geometric fidelity, or suppress diagnostics merely to improve a timing result.
- Preserve transactional behaviour: validate replacement geometry before committing document changes, and keep failure paths recoverable.
- Do not change tests only to make an implementation pass. When an intended change invalidates an assertion, explain why and obtain agreement on the new invariant.

## Performance work

- Follow `reference/PERFORMANCE_SOP.md`; do not invent a reduced benchmark procedure for an individual change.
- Use the B14 **Whole-process benchmark** as the current operator-visible baseline and compare equivalent starting state, settings, stage sequence and cache state.
- Measure both ordinary editing and deferred Validate/Export work so cost is not merely hidden at a later boundary.
- Preserve cache signatures and invalidation rules. A faster stale result is a correctness failure. Test both initial calculation and unchanged-result reuse when touching caches.
- Minimise redundant document recomputes, metadata writes, display-object creation, shape construction, and repeated traversals only when output equivalence is demonstrated.
- Keep FreeCAD object creation out of per-chair or similar hot loops where batching/compounds preserve the same result; the B15 structural test enforces this for the lightweight chair display.
- Do not introduce threads or processes around FreeCAD document or GUI operations without explicit approval and a dedicated correctness test.
- If a requested performance readout is visible only in the user's UI, ask for the copied report instead of inventing or estimating its values.

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

- These commands were verified with FreeCAD 1.1.1 in the current environment.
- A successful FreeCAD smoke run must print `B15 FreeCAD 1.1 headless smoke test passed`; an exit code without that sentinel is not evidence that FreeCAD executed the assertions.
- `tests/validate_b15.py` treats B14 as a baseline. If B14 is deliberately changed, do not automatically alter B15 or the comparison test merely to restore a pass; first determine the intended version scope.
- Headless checks do not replace a real GUI workflow run. For geometry, document integration, display, export, or performance changes, run the exact target macro in FreeCAD and exercise the affected guided stages.

## Completion and review

- Before reporting completion, inspect the diff for accidental broad changes and run every applicable check above.
- State which macro/version changed, which invariants were preserved, which tests ran, and any GUI validation still required.
- For project-plan work, state the current phase, which deliverables or gates changed, and whether the phase remains open or was accepted closed.
- For performance changes, include the before/after reports and identify any measurement noise or cache-state difference.
- Keep `.idea/`, `.venv/`, `__pycache__/`, generated FreeCAD documents, exported production files, and temporary benchmark artifacts out of commits.
- Do not commit or push unless the user asks.
