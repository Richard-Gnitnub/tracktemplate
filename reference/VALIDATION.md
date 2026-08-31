# Validation Strategy

## Purpose

Validation protects railway correctness while the macro is optimised and
separated into architectural layers. Tests must distinguish analytical
correctness, FreeCAD integration, display behaviour and production output.
[TESTING_POLICY.md](TESTING_POLICY.md) defines the project-wide obligation to
add tests and the limited circumstances in which an existing test oracle may
change.

## Document boundary

This document owns durable validation layers, evidence-interpretation rules,
stable runner profiles and entry points, and the minimum change matrix. Change
it only when one of those owned contracts changes.

A new test, completed run, benchmark result or current-phase proof does not by
itself justify changing this document. Put executable detail in the affected
test or runner, evidence required by the
[Level 2 or Level 3 documentation lifecycle](ENGINEERING_POLICY.md#documentation-lifecycle)
in [current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md), and bounded
measurement results in a dated report under `reference/benchmarks/`. Do not use
this document as a tranche log.

The existing detailed command catalogue remains pending a separate bounded
simplification because it contains retained validation obligations. This
boundary controls new changes now and does not authorise further per-tranche
additions.

## Current version roles

- `AdvancedTurnout.FCMacro` is the immutable B14 legacy comparison oracle (`10.2A8A7B14`).
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro` is the accepted B15 behavioural reference entering Phase 1 (`10.2A8A7B15`).
- `10.2A8A7B16` identifies the current modular development checkpoint. Its
  small `TrackTemplate.FCMacro` composition root routes the bounded three-
  function transition calculation exclusively through the modular domain.
  The inherited B15 GUI host remains a lazy compatibility dependency, while
  dual-route comparison is development-only oracle tooling. This is not the
  public Workbench/RC version.
- `tests/validate_b15.py` validates B15 structure/analysis, compares selected
  railway functions, and proves complete inherited-module AST parity with B14
  after normalising only version, launch, docstring, and recompute-instrumentation
  differences.
- `tests/freecad_validate_b15.py` exercises the B15 chair display path in real headless FreeCAD.
- `reference/contracts/phase1-compatibility.json` defines the exact currently
  qualified FreeCAD stack, standalone Python floor and bounded B14/B15 future
  migration ingress. It is a Phase 1 control, not an implemented migrator or
  final Addon manifest.

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
- For the legacy macros, run the Phase 1 structural inventory/validator to
  detect drift in duplicate definitions, captured aliases, import-time method
  patches, mutable-state signals and selected caller/dependency closures.
- For retained source-organisation changes, review the named authoritative
  implementation, genuinely shared invariant, narrow interface, dependency
  direction and any temporary duplicate/retirement condition.
- `tests/validate_phase2_foundation.py` and `tools/modular_structure.py` fail
  on a forbidden domain/platform import, undeclared or prohibited layer edge,
  circular dependency, speculative module or import-time structural warning.
  Retain and extend these guards with every applicable package change.
- Treat structural metrics as risk signals, not proof of maintainability;
  railway-semantic cohesion and abstraction quality still require review plus
  behavioural evidence.

### 2. Analytical validation

- Exercise pure calculations without depending on a FreeCAD GUI.
- Compare geometry records, topology, timbers, chairs, findings, stable identities and deterministic ordering.
- Test cache misses, valid reuse and invalidation after every relevant input class changes.

### 3. FreeCAD document validation

- Use an exact host profile that the Phase 1 compatibility contract qualifies.
  The contract qualifies only the exact Linux x86_64 stable
  `org.freecad.FreeCAD` Flatpak profiles for FreeCAD 1.1.1 and 1.1.3. The two
  profiles contain CPython 3.13.14, PySide6/Qt 6.10.3, OpenCASCADE 7.8.1, and
  Coin 4.0.8. FreeCAD 1.1.2 and all other host profiles are not qualified.
- Make sure that object types, properties, groups, visibility, transactions,
  recomputes, and cleanup are correct.
- Make sure that save and reopen behaviour is correct when persistence changes.
- Make sure that transient validation or export objects do not stay in the
  editable document.

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

## Verified commands and CI

Run from the repository root.

### Developer-tool boundary

The project virtual environment contains the Python packages for standalone
TrackTemplate development and repository validation. `requirements-dev.txt`
contains optional packages for local repository and agent-skill validation.
These packages are not Addon dependencies. The project virtual environment
and qualified FreeCAD profiles have different controls for their Python
packages.

Ruff is an optional developer validation executable. TrackTemplate has no root
Ruff configuration, CI step or version contract. Thus, Ruff is not necessary
for TrackTemplate validation. If Ruff is on the user `PATH`, an agent can use
it to examine changed, non-frozen Python files. The Ruff operation must not
change files. Report the executable path and version. The project owner must
authorise a Ruff installation or version change. Do not change `.venv` or a
qualified FreeCAD environment only to get Ruff. The tracked configuration or
CI must define the repository version contract before Ruff becomes necessary.

A user-level tool manager such as `uv` can supply a developer executable. The
`uv` executable has no TrackTemplate package-management role. Do not use
`uv init` in this repository. Do not add a root `uv.lock`. The project owner
must authorise a package-management migration in a different task.

### Programmatic regression pipeline

Use the local pipeline as the normal concise entry point for retained
regressions:

```bash
.venv/bin/python tools/run_regression_pipeline.py
.venv/bin/python tools/run_regression_pipeline.py --profile transition
.venv/bin/python tools/run_regression_pipeline.py --profile transition-gui
```

The default `standalone` profile parses every tracked Python and macro source
and runs the complete clean-checkout standalone matrix. The `transition`
profile adds the qualified headless transition persistence, Coin-scene and
edit-lifecycle checks. The explicit `transition-gui` profile adds the isolated
real-GUI ViewProvider workflow. Profile names describe durable behaviour, not
phase acceptance; phase-prefixed test paths may be renamed when their boundary
stabilises without retiring their contract.

Each step requires both a zero exit status and its documented success sentinel.
Raw output is retained under ignored
`benchmark-output/validation-pipeline/` run directories while the terminal
emits only step results and `TRACKTEMPLATE_REGRESSION_PIPELINE=`. The pipeline
stops before later, more expensive layers after a failed prerequisite; the
standalone runner itself still completes every standalone validator so one log
exposes all observed failures.

The qualified and GUI profiles are workstation evidence, not clean-checkout
CI. The GUI profile remains explicit and does not establish screenshot hashes,
numerical timing gates or a mandatory GUI-host workflow.

The tracked [standalone CI workflow](../.github/workflows/ci.yml) runs on pushes
to `main` and pull requests. It parses every tracked Python/macro source, then
runs every `tests/validate_*.py` check through the complete-run standalone
runner. The runner continues after a failed validator and emits a structured
summary so one run exposes all observed failures.

Use the same explicit profiles locally:

```bash
.venv/bin/python tools/run_standalone_validators.py --profile ci
.venv/bin/python tools/run_standalone_validators.py --profile local
```

The `ci` profile proves deterministic tracked contracts in a clean checkout.
It tests that a missing ignored critical asset fails closed, but does not
pretend the asset is available. The `local` profile additionally requires the
workstation-only archive, hash, branch and upstream evidence. Neither profile
substitutes for selected FreeCAD, GUI, backup/restore, output or owner-decision
evidence.

Run the same source parser locally when diagnosing a syntax failure:

```bash
.venv/bin/python tools/validate_python_syntax.py
```

Fast B15 structural and analytical validation:

```bash
.venv/bin/python tests/validate_b15.py
```

Real FreeCAD 1.1 headless B15 smoke test:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD tests/freecad_validate_b15.py
```

Durable modular package, domain/API and foundation checks:

```bash
.venv/bin/python tools/modular_structure.py
.venv/bin/python tests/validate_phase2_foundation.py
```

Product-system ontology structure, controlled codes, semantic invariants and
human/formal coverage:

```bash
.venv/bin/python tests/validate_ontology.py
```

This standalone standard-library validator checks the supporting JSON-LD/OWL
projection and its Markdown reference. It does not replace the canonical
architecture, schema validators, railway tests, FreeCAD integration evidence
or current phase and authority records.

Current Phase 3 transition routing and rollback boundary:

```bash
.venv/bin/python tests/validate_phase3_transition_routing.py
```

This standard-library check exercises complete synthetic legacy, modular and
legacy change-back routes and fail-closed source, contract, API and launch
boundary cases. It also requires the compatibility adapter to remain in the
declared dependency layer without structural warnings.

Phase 3 routed full-workflow harness contracts:

```bash
.venv/bin/python tests/validate_phase3_transition_workflows.py
.venv/bin/python tests/validate_phase3_transition_performance.py
```

The first command protects the reusable driver seam, exact B14/B15
fingerprints, B16 route loader, four-process controller, five-field volatility
boundary, scenario order, preference restoration, bounded B14-to-B15
generator-version handling and exact semantic comparison. The second protects
the 202-case calculation boundary, profiled action selection, repetition/order
rules, descriptive comparisons and committed evidence links. Neither starts
FreeCAD.

Accepted Phase 2 FreeCAD loading and zero-document-mutation smoke:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase2_foundation.py
```

The standalone validator also launches an isolated interpreter with FreeCAD,
Part, Qt and pivy imports blocked. The Phase 2 FreeCAD smoke must print
`Phase 2 FreeCAD foundation smoke test passed`. It loads the launcher
definitions without executing the current orchestration entry point, then
checks package/API/domain resolution, exact runtime qualification and zero
document mutation. This keeps the accepted loading check independent of later
calculation and caller-routing status.

Phase 3 oracle and authorised Phase 4 comparison-route retirement:

```bash
.venv/bin/python tests/validate_phase3_transition_routing.py
.venv/bin/python tests/validate_phase4_transition_route_retirement.py
```

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase3_transition_slice.py
```

The Phase 3 standalone test retains legacy → modular → legacy comparison only
through `tools.phase3_transition_pilot`. The Phase 4 retirement validator
requires that oracle to remain outside the product package, removes the route
argument and legacy exports from current composition, and proves that the
modular-only host loader is a clean, lazy compatibility dependency.

The FreeCAD test executes the current B16 default and requires that it neither
loads the 2.3 MB B15 host nor mutates a document. It rejects the retired legacy
argument before host loading, reproduces the accepted all-caller parity through
the development-only oracle, then loads a separate product session and proves
that all three bindings are the modular API with no comparison route. It must
print `Phase 3 transition routing FreeCAD smoke test passed`. No operator dialog
is launched by this smoke, and the immutable B14/B15 workflow evidence remains
the accepted GUI oracle. Do not rewrite the independent Phase 2 loading smoke.

Phase 4 transition canonical-state foundation:

```bash
.venv/bin/python tests/validate_phase4_transition_state.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_transition_state.py
```

The standard-library validator owns the accepted bounded-read schema-v1 deterministic
round-trip, complete transition-analysis signatures, cold/reuse/change-back,
label-only reuse, numerical invalidation, stable identity, stale/corrupt
derived-result recovery, fail-closed input cases and application dependency
boundary. The qualified-FreeCAD smoke proves only runtime/type compatibility,
the same exact JSON round-trip and zero document mutation. It is not FreeCAD
property, transaction, Undo/Redo or FCStd save/reopen evidence.

Phase 4 qualified FreeCAD transition persistence:

```bash
.venv/bin/python tests/validate_phase4_transition_persistence.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_transition_persistence.py
```

The standalone check protects the concrete-adapter dependency direction,
property/type contract, qualified-write boundary and disposable fixture scope
without importing FreeCAD. The FreeCAD test uses only newly created disposable
documents and a temporary FCStd. It proves exact canonical save/reopen, stable
identity independent of name/label/order, one-command create/update history,
create/update Undo/Redo, no-op history, preflight rejection, injected
post-write rollback, stale/corrupt derived-result handling, foreign-object
preservation and rejection of unqualified runtime evidence. Its success
sentinel is `Phase 4 transition FreeCAD persistence validation passed`.

Phase 4 B14/B15 legacy-document detection:

```bash
.venv/bin/python tests/validate_phase4_legacy_document_detection.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_legacy_document_detection.py
```

The standalone matrix proves deterministic B14-only, B15-only and accepted
mixed-window reporting; foreign-object exclusion; versionless/future
inspection-only results; malformed/conflicting fail-closed results; exact
contract gating; isolated import; and zero outer-detector write authority. The
FreeCAD test uses only newly created disposable documents and a temporary
FCStd. It proves zero mutation during inspection and an identical mixed report
after save/close/reopen. Its success sentinel is
`Phase 4 legacy document FreeCAD detection validation passed`. This is outer
ingress evidence only: even when one exact family is separately qualified, the
detector remains inspection-only and cannot advertise a whole document as a
supported migration source.

Phase 4 read-only plain-line transition family assessment:

```bash
.venv/bin/python tests/validate_phase4_plain_line_transition_assessment.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_plain_line_transition_assessment.py
```

The standalone matrix consumes the accepted outer detector and proves exact
B14, B15 and expected-mixed handling for the spacing-matched secondary
plain-line transition slice. It requires complete typed settings, derives
stable identities from template-set identity plus persisted semantic track
ordinal and end, replays the canonical solver exactly, rejects partial,
unsupported, corrupt or ambiguous input, and retains zero write, migration or
production authority. The FreeCAD check opens the reproducible ignored B14
base fixture read-only, obtains the two exact canonical candidates, compares
document/property/history snapshots and requires the source FCStd hash to stay
unchanged. Its sentinel is
`Phase 4 plain-line transition FreeCAD assessment passed`. This read-only
assessment does not itself authorise a copied-target write or advertise family
support; the registry and fixture below own those separate controls.

Exact-family Phase 4 copied-target transition migration fixture:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_plain_line_transition_migration.py
```

This isolated fixture starts B14, B15-only and expected mixed targets as
physical copies of disposable source FCStd files. The host-independent
operation requires exact family-level source/target assessments before it calls
the injected qualified FreeCAD writer once to create both canonical transition
records in one batch transaction. The fixture requires one-step Undo/Redo,
duplicate preflight with no history, exact canonical and legacy persistence
through target save/reopen, source-byte preservation, and complete abort after
an injected failure on the second payload. It also requires the original
reproduced B14 fixture hash to remain unchanged; requires
`SUPPORTED_MIGRATION_FAMILIES` to contain exactly
`plain-line-spacing-matched-transition-intent`; requires migration support to
be true only for that family; and requires production-output authority to
remain false. Its sentinel is
`Phase 4 copied-target transition migration fixture passed`. Passing this test
proves the exact fixture-only family boundary; it does not qualify a complete
document or authorise a Workbench/operator migration path.

Exercise the same persistence and rollback fixture inside an isolated real-GUI
process, with the GUI-host boundary asserted, using:

```bash
tools/freecad_bridge/run-isolated \
  tools/freecad_bridge/freecad-cli execute-code \
  'assert __import__("FreeCAD").GuiUp; import runpy; runpy.run_path("tests/freecad_validate_phase4_plain_line_transition_migration.py", run_name="__main__")'
```

Use `runpy.run_path` rather than `execute-code --file` for this validator
because the latter bridge mode does not define `__file__`. A successful JSON
bridge response must contain the same fixture sentinel. This is real-GUI host,
document-lifecycle, persistence and rollback evidence for the exact supported
fixture-only family; it is not evidence of an operator-visible command,
target-path control or production output.

Phase 4 neutral chair-definition package:

```bash
.venv/bin/python tests/validate_phase4_chair_definition.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_chair_definition.py
```

The standalone validator owns chair-package schema v1, the explicitly
non-prototype synthetic fixture, deterministic signed round-trip, exact source
and canonical decimal quantities, unit conversion, fixed chair-local frame,
datum/component/procedure/rail-interface references, manufacturing separation,
lineage coverage, acceptance, external dependency-manifest linkage and the
missing/corrupt/unsupported/ambiguous failure matrix. It also requires the
synthetic manifest to pass the existing strict project-clearance validator,
then proves Phase 9 production admission still blocks geometry, document and
filesystem mutation. The qualified-FreeCAD test proves only bundled-Python
compatibility, the same exact package round-trip and zero document mutation;
its sentinel is
`Phase 4 chair-definition FreeCAD compatibility validation passed`. Neither
test supplies an S1 definition, runs a chair builder or qualifies output.

Current Phase 3 real-GUI workflow parity:

```bash
tools/freecad_bridge/run-phase3-transition-workflows \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

This runs plain-line editing and connected-straight lifecycle automation under
the complete legacy and modular routes in four fresh isolated GUI processes.
It requires exact route-independent workflow contracts, preserved route
bindings, undo/redo, save/reopen, isolated preference restoration, source
non-mutation and the plain-line invalid-input/transaction-abort recovery paths.
It records raw timing observations but is not the contracted calculation or
workflow performance profile.

Current Phase 3 contracted performance profile:

```bash
.venv/bin/python tools/phase3_transition_performance.py \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

This performs nine same-process repetitions per route of the complete frozen
202-case calculation grid, then three fresh isolated FreeCAD GUI repetitions
per workflow and route. It alternates route order, retains exact workflow
parity and records medians, ranges, CPU, end-minus-start RSS and object deltas.
The 12-process GUI profile is checkpoint evidence rather than a fast test. Its
timings do not establish an interaction budget or an optimisation claim; raw
paths, FCStd files and JSON remain ignored, with a sanitised committed report
under `reference/benchmarks/`.

Retained Phase 5 bounded Coin resource profile:

```bash
.venv/bin/python tests/validate_phase5_transition_coin_resource_profile.py
.venv/bin/python tools/phase5_transition_coin_resource_profile.py
```

The fast standard-library validator protects the fixed 32-object fixture,
three-process minimum, cold/warm measurement fields, stable identity and scene
counts, cache reuse, zero-`Shape` and cleanup contracts without importing
FreeCAD. The profiler runs three fresh isolated qualified FreeCAD GUI
processes. Each constructs 32 logical objects and preview layers, performs one
untimed warm-up and three measured unchanged refreshes, and records wall time,
process CPU, explicit recompute duration, end-minus-start RSS, actual Coin-layer
and active-node counts and individual samples. Correctness invariants are
gates; timings remain descriptive and establish no representative workload,
capacity or numerical budget. Raw JSON and logs remain ignored. The sanitised
result and limitations are in
[benchmarks/2026-07-29-phase5-transition-coin-resource-profile.md](benchmarks/2026-07-29-phase5-transition-coin-resource-profile.md).

Retained Phase 5 bounded transition interaction/resource range profile:

```bash
.venv/bin/python tests/validate_phase5_transition_interaction_range_profile.py
.venv/bin/python tools/phase5_transition_interaction_range_profile.py
```

The fast standard-library validator protects the five declared scale points,
three-fresh-process minimum, host-independent result validation, exact object,
layer, node, mapping, edit-isolation, Undo and cleanup invariants, and explicit
non-acceptance boundary without importing FreeCAD or Qt. The profiler repeats
the qualified Entry/Exit family unit at 1, 2, 4, 8 and 16 set counts, giving
2–32 logical objects. A test-only view grid makes the repeated local-frame
previews separately hittable without changing canonical state or product
placement.

At every scale, each of three fresh isolated qualified GUI processes performs
one real Qt pointer selection, opens the transient parameter editor, enters one
length through real keyboard/button input, verifies one selected-only edit and
one Undo, then disposes every cache, proxy and document. It records cold,
selection, dialog, edit, Undo and cleanup wall/CPU/end-minus-start-RSS fields.
Correctness invariants are gates; values remain descriptive and do not accept a
capacity, interaction budget, renderer or optimisation. The sanitised method,
observations and limitations are in
[benchmarks/2026-07-31-phase5-transition-interaction-range-profile.md](benchmarks/2026-07-31-phase5-transition-interaction-range-profile.md).

Retained Phase 5 representative Entry/Exit multi-object editing workload:

```bash
.venv/bin/python tests/validate_phase5_transition_parameter_editor.py
.venv/bin/python tests/validate_phase5_transition_multi_object_edit.py
tools/freecad_bridge/run-phase5-transition-viewprovider
```

The standalone parameter-editor validator proves the internal length command,
fail-closed selection controller and accepted UI dependency direction without
importing Qt or FreeCAD. The multi-object validator fixes the workload rationale
and protects the real-GUI proof and runner. The representative boundary is the
smallest complete currently qualified plain-line transition family shape: one
secondary track produces one canonical Entry and one canonical Exit record.
Distinct deterministic transition lengths make those two development previews
pointer-disambiguable; they are not product defaults.

The existing isolated ViewProvider runner first retains the one-object
lifecycle/save-reopen proof, then exercises the two-object workload in the same
qualified real-GUI process from a new empty document. A real Qt mouse click
must select the red Exit preview and resolve its stable domain identity. A
modeless dialog parented to the FreeCAD main window must show that identity and
its current transition length. Real Qt keyboard input and an Apply-button click
must route one length edit through the internal application command. Undo,
Redo, an injected refresh failure and a cleared-selection attempt must change,
recover or reject only as intended while the Entry state/cache remains
untouched. Applying the unchanged displayed value must create no history. The
failure must remain visibly diagnostic and the no-selection attempt must change
neither state, history nor cache counters. Selected and edited dialog captures
are retained for visual inspection. Every state must retain two compact
`App::FeaturePython` objects, two Coin layers, 14 active selectable-scene nodes,
zero `Shape` properties and identical stable selection mappings. The runner
requires the inner
`TRACKTEMPLATE_PHASE5_MULTI_OBJECT_EDIT_GUI=` result and emits the existing
outer `TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=` sentinel.

This workload is representative only of the currently qualified fixture-only
family shape. It does not establish whole-layout capacity, an interaction
budget, automatic product load or menu wiring, renderer suitability or owner
acceptance.

Retained Phase 5 post-open attachment and explicit B16 lifecycle boundaries:

```bash
.venv/bin/python tests/validate_phase4_transition_persistence.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_transition_persistence.py
.venv/bin/python tests/validate_phase5_transition_coin_viewprovider.py
.venv/bin/python tests/validate_phase5_transition_editing_lifecycle.py
tools/freecad_bridge/run-phase5-transition-viewprovider
```

The persistence checks protect and exercise the read-only
`read_transition_objects(document)` adapter operation. Qualified FreeCAD must
ignore foreign records, validate every canonical transition record, reject
duplicate stable identities, return `(object, state)` pairs in transition-ID
order and change no property or Undo/Redo state.

The ViewProvider checks cover the explicitly invoked
`TransitionCoinDocumentAttachmentFixture`. The host-independent proof uses two
records supplied out of order, refreshes only one retained cache, restores
both original default proxies on disposal and clears every live binding and
cache after an injected second-object attach failure. The isolated real-GUI
proof saves and reopens one canonical record, confirms that no transient
attachment marker was persisted, injects and recovers from a Coin attach
failure, then invokes the document attachment once. It requires a new cache
and ViewProvider with an equivalent preview, a reused no-op refresh, visible
rendering, cleared derived state on disposal, restored host proxy and unchanged
canonical JSON, property lists, object count and history throughout.

The same runner then proves the
saved/reopened representative Entry/Exit attachment boundary. It first
disposes the two manual editing fixtures and caches, saves only the two
canonical `App::FeaturePython` records, closes and reopens the FCStd, and
invokes the document attachment explicitly. The attachment must enumerate
Entry then Exit by stable identity, rebuild two new equivalent caches and Coin
layers, preserve both pre-save selection mappings, and reuse an unchanged Exit
refresh after deliberately discarding Entry's cache as an observable sibling
trap. Entry's cache must remain missing while its bound source signature,
selection root and mapping remain unchanged. The attachment must retain two
objects, two logical layers, 14 active selectable-scene nodes, zero `Shape`
properties and zero attachment history delta. Batch disposal must clear both
caches and selection roots, restore both original host proxies and leave the
reopened canonical JSON, property lists, object count and history unchanged.
The known empty-switch-child limitation applies independently to both disposed
records.

The attachment remains an internal, injected lower boundary and is absent from
`tracktemplate.api` and package initialisation. The standalone lifecycle check
additionally protects the explicit `TrackTemplate.FCMacro`
`activate_transition_editing()` route. The macro's normal
`FOUNDATION_RESULT = run_macro()` path remains unchanged and imports no host,
Coin or Qt module unless that function is called. Activation must attach a
non-empty stable-ID set once, reject active duplication, reuse one transient
editor, clear only the target document's selection, retry partial attachment
and observer cleanup, and retire without reactivation. Composition-level fault
injection must prove that observer-registration rollback remains recoverable
and that a failed observer removal retains the same observer for a successful
retry. It also protects the versioned development contract and keeps the
coordinator in the host-independent UI layer.

The same existing isolated runner adds one third, focused real-GUI proof after
the retained one-object and representative workflows; it does not create
another orchestration loop. On the qualified Entry/Exit document, the explicit
macro route must attach both transitions once, leave canonical JSON, built-in
property lists, history, `Shape` count and the captured public `DisplayMode`
state unchanged, reject a concurrent invocation, expose the existing editor,
and preserve one edit with Undo/Redo. The transient document observer is
registered only by successful explicit activation. A save must invoke
FreeCAD's `slotStartSaveDocument`, retire the lifecycle before serialization,
remove the observer, clear the target selection without clearing a selected
sibling document, clear caches, proxies and active Coin children, and persist
no transient marker. Close/reopen must then reconstruct new scene nodes and the
original owner-visible Exit state after another explicit activation. Explicit
deactivation must retire that rebuilt lifecycle before direct document close;
the bounded composition adds no automatic close or permanent loading policy.
The inner sentinel is
`TRACKTEMPLATE_PHASE5_TRANSITION_EDITING_LIFECYCLE_GUI=`; the outer runner
sentinel remains `TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=`.

FreeCAD exposes display-mode registration but no qualified Python removal
operation. Disposal therefore restores the original public display-mode
enumeration and switch selection and clears every retained mapping and cache,
but leaves one named empty switch child. The lifecycle confines that residual
to one child per object, rejects same-document reactivation without adding a
second child, and relies on document close/reopen to remove it. The checks
require this documented bounded limitation rather than describing disposal as
complete view-state restoration. D-P5-002 accepts it only for the demonstrated
Entry/Exit boundary recorded in the
[frozen Phase 5 closeout](history/phase-closeouts/PHASE5_CLOSEOUT.md#phase-5-coin-renderer-and-editing-acceptance-panel).
Passing the checks alone grants no renderer, phase, startup, Workbench/menu,
migration, release or output authority.

Phase 6 adapter-neutral Entry/Exit exact-centreline contract:

```bash
.venv/bin/python tests/validate_phase6_transition_exact_contract.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase6_transition_exact_contract.py
```

The standalone proof covers the explicit caller-owned chord-error tolerance
and segment ceiling, canonical local left-turn frame and units, deterministic
station ordering, conservative Euler-curvature interpolation bound,
independent high-precision Fresnel-series coordinates, zero-length and
fail-closed resolution cases, signed result reuse/change/change-back and
failure atomicity. The qualified FreeCAD smoke proves the additive public
contract runs in the accepted host profile without creating a document,
object, property or Undo/Redo change. Its sentinel is
`Phase 6 transition exact qualified FreeCAD validation passed`. This route
creates no `Part` geometry, target-format output, production clearance,
operator workflow or Phase 6 exit evidence.

Phase 6 transient Entry/Exit exact geometry:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase6_transition_exact_geometry.py
```

This qualified-host proof constructs the verified exact centreline as one open
`Part` wire, or one vertex for zero length, on a single `Part::Feature` in a
hidden temporary document. It checks ordered coordinates, bounds, polyline
length, topology, planarity, kernel validity and deterministic signed neutral
measurements. Success, cancellation, cancellation-check failure and injected
Part-build failure must all close the temporary document, restore the prior
active document and leave the editable document, its properties and Undo/Redo
history unchanged. Its sentinel is
`Phase 6 transition transient exact geometry validation passed`. No
`Part.Shape` crosses the adapter, no file is written, and the result supplies
no GUI, target-format, production-clearance or Phase 6 exit acceptance.

Phase 6 private-development Entry/Exit DXF transaction and import:

```bash
.venv/bin/python tests/validate_phase6_transition_dxf_export.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase6_transition_dxf_export.py
```

The standalone proof covers deterministic DXF and dependency-manifest bytes,
descriptor-relative destination control, resolve-to-bind removal and
substitution, post-lock substitution, directory-rename and symbolic-link
races, anonymous creation-bound staging and observed descriptor-close
abandonment, surviving-host `BaseException` propagation with chained truthful
retained-state diagnostics, preservation of the original interruption when
an anonymous close itself fails, best-effort remaining anonymous closes and
non-replacing bound-directory close diagnostics, non-recoverable
post-link/pre-sync durability uncertainty, exact zero-member, DXF-only,
manifest-only and complete-pair states, inert historical controls,
interruption after each addition, next-invocation monotonic completion,
required directory synchronisation before
complete-pair reuse and fail-closed preservation when that synchronisation
fails, cancellation and injected failure after one addition,
initial-member and post-addition substitution, unsupported primitives,
complete exact-set reuse, non-regular-final and byte-collision refusal, active-lock
fail-closed diagnostics and truthful retained-state
diagnostics. It proves the bounded D-P6-003 strict add-only, journal-free
implementation without granting deletion authority: no published final is
removed, rewritten or replaced by TrackTemplate. The standalone sentinel is
`Phase 6 transition DXF export validation passed`. The qualified FreeCAD proof
imports both the non-zero `LWPOLYLINE` and zero-length `POINT`, and repeats
document isolation, cancellation, injected second-addition failure, exact
partial preservation and next-invocation completion, plus surviving-host
interruption cleanup. Its required sentinel is
`Phase 6 transition DXF qualified FreeCAD validation passed`. These commands
remain bounded to the accepted Entry/Exit slice and private-development
`unknown` output; they supply no GUI, production-output, Phase 6 exit or release
acceptance.

#### Supported exporter interruption evidence

Exporter interruption evidence is interpreted against the canonical
[supported exporter failure model](ARCHITECTURE.md#supported-exporter-failure-model)
and the operator procedure in
[Recovery after an abnormally interrupted export](RECOVERY_AND_BACKUP.md#recovery-after-an-abnormally-interrupted-export).
The existing Phase 6 exporter commands above remain the durable entry points;
this section does not create a second command catalogue.

Mandatory retained evidence covers ordinary exceptions, explicit application
cancellation, the expressly retained `BaseException` boundaries, and the
accepted staging, publication, durability, cleanup and recovery matrix. It
must preserve every pre-existing and published final, prove conservative
diagnostics when durability or retained state is uncertain, exercise
exact-partial and exact-complete next-invocation handling under D-P6-003, and
retain qualified FreeCAD import and host-execution evidence within the
documented platform and filesystem profile. Process-termination evidence is bounded to
the operating-system process boundary where process-owned descriptors and
advisory locks are released; restart alone is not destination-validation
evidence.

Retained mandatory tests and exploratory disposable probes have different
authority. A probe outside the supported model may inform future architecture,
but arbitrary asynchronous injection at an excluded instruction-level
micro-window does not automatically become an implementation defect or Exit 3
blocker. It does become a blocker when it demonstrates deletion, overwrite,
corruption, unsafe mutation, failure of a supported workflow or accepted
recovery boundary, unsafe retry, a false diagnostic or another retained
mandatory-invariant violation. Current tranche chronology, temporary line
numbers and individual probe narration do not belong in this durable contract.

Repository recovery and ignored-data safety controls:

```bash
.venv/bin/python tools/repository_safety_audit.py
.venv/bin/python tests/validate_recovery_controls.py
.venv/bin/python tests/validate_recovery_controls.py --live-workstation
```

The audit is read-only and performs no network operation. It reports clean and
pushed checkpoint state from local remote-tracking refs, verifies the ignored
Templot source archive, inventories local generated-data roots and fails closed
when a requested backup target is absent, inside the repository or on the same
mounted filesystem. The default validator proves deterministic control
behaviour, including rejection of a clean fixture without the archive. The
`--live-workstation` profile additionally proves the current checkout's ignored
archive/hash and branch/upstream boundary. Neither result claims that an
independent backup or restore exists.

If you do not know the accepted commit for `origin/main`, use `git fetch`.
Before a bounded cycle with recovery risk, make sure that the checkpoint has
tracked cleanliness. Before the cycle, make sure that a branch on GitHub
contains the checkpoint commit:

```bash
.venv/bin/python tools/repository_safety_audit.py --require-checkpoint
```

Before worktree retirement, use the retirement audit with
`--retirement-worktree` and without a retirement plan. Record the SHA-256 and
counts for the local-state inventory in phase evidence. Examine the retirement
plan with the
[worktree retirement procedure](RECOVERY_AND_BACKUP.md#worktree-retirement).
Use the retirement audit again with `--retirement-plan` and
`--require-retirement-ready`. Make sure that the sentinel is
`TRACKTEMPLATE_WORKTREE_RETIREMENT=` with `retirement_ready: true` and no
finding.

The recovery validator must give a `FAIL` result for each invalid state. The
recovery validator must include these invalid states:

- The pull-request state `MERGED` and tracked cleanliness without a retirement plan
- A local-state inventory item that the retirement plan does not contain
- An item in 2 or more local-state types
- Ambiguous or uniquely owned state
- A change to the worktree, accepted commit, or local-state inventory
- A worktree without tracked cleanliness
- A local-state type that is not one of the 5 local-state types
- Missing evidence that no person or process uses the worktree
- Missing removal authority
- An `assume-unchanged` or `skip-worktree` value in the Git index
- A Git command that uses an environment variable with the `GIT_` prefix to
  select a different repository or Git index
- An item without a canonical owner or result
- Different bytes in the source file and copy
- A different value for `accepted_ref`
- A duplicate key in the retirement plan
- A symbolic link in the path for planned preservation
- Data from the retirement plan in command output
- A local path from a file-system error in command output
- Information from a Git error in command output
- A command in the retirement audit that changes Git state or local files
- A retirement audit that uses a command with `--force`.

The recovery validator must use a temporary repository. In the temporary
repository, the validator must use `git worktree remove` without `--force`.
The validator must make sure that the authoritative local source stays
available. Before branch removal, the validator must show that
`git worktree list` does not contain the worktree. Before branch removal, the
validator must also show that the accepted commit contains the branch tip.

Before worktree removal, the validator must examine the local-state types in the
retirement plan. Before worktree removal, the validator must examine the
preservation diff for the local-state inventory. After worktree removal, the
validator must show that no other branch changed.

After worktree removal, the validator must show that no other worktree changed.
After worktree removal, the validator must show that the stash inventory did not
change. After worktree removal, the validator must show that files at each
location for planned preservation did not change.

The retirement audit does not classify a local-state inventory item. The recovery
validator gives no removal authority.

Assess a selected or replacement external destination only with
`--backup-target ... --require-backup-target`; backup completion and restore
evidence remain separate recovery conditions under
[RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md). The first repository-scope
copy, restore and incremental-repeat result is recorded in the linked
2026-07-22 evidence there for the owner-confirmed complete project-data scope;
the audit command by itself still does not prove those executed results.

Repository QA, documentation-link and residual-risk controls:

```bash
.venv/bin/python tests/validate_quality_assurance.py
```

This standard-library check protects the canonical QA and learning-document
roles, verifies the accepted hash manifest for frozen phase/audit/benchmark
records, reconciles the frozen audit's open QA dispositions with
`current/risks.json`, verifies every repository-internal Markdown file target
and preserves the immutable B14/B15 fingerprints. It also enforces the
`AGENTS.md` size/routing boundary, three-level task model, governance budget,
Level 3 true-gate panel triggers and compact completion report in
[ENGINEERING_POLICY.md](ENGINEERING_POLICY.md). It proves control consistency
only; it does not close an open risk or accept a phase closure.

The check also examines the
[ASD-STE100 Issue 9 reference-source instructions](external/asd-ste100/README.md),
their Git-exclusion boundary, and the different functions of policy and an
external reference. Normal CI does not use the ignored PDF. A conformance
record must report its official source. Automatic validation does not prove
linguistic conformance.

### Validation of the retrieval contract

The retrieval contract has a source manifest and a retrieval index. The
Technical Documentation Profile owns full applicability. The technical-term
register owns technical terms.
Validate the retrieval contract without the PDF with:

```bash
.venv/bin/python tests/validate_ste100_retrieval.py
```

When the authorised source is available at the local path, also use:

```bash
.venv/bin/python tools/ste100_lookup.py rebuild
.venv/bin/python tools/ste100_lookup.py validate
```

The local check must fail closed when the source is missing. It must also fail
closed when its byte size or SHA-256 identity is different from the source
manifest. The PDF extractor file owner can be root or the current user. It must be a
regular file. It must not be in the repository or active
Python environment. Its group and other users must not have write access. A
rebuild must reject all other PDF extractors. It must reject a
source-derived index when its identity is not the identity in the source
manifest.

The derived cache must contain metadata only. It must have the same input
identities as the source, profile, technical-term register, retrieval index,
manifest, tool, and PDF extractor. The tool must accept the cache schema version. Source
mode must use verified source bytes. It must use the PDF extractor identity
that the derived cache records.

Include tests for the source, derived cache, retrieval index, technical-term
status, and each output limit.

The validator must not make a linguistic conformance, certification, or
endorsement claim. A reviewer can use a review receipt to record a review of
full applicability. The review receipt must record that the reviewer examines
the complete applicable requirement set. The review receipt, pre-check, derived
cache, and selected lookup results do not show that this review occurred. They
also do not show conformance. Source identity validation does not make a
positive rights claim.

For each material change to canonical prose, validate the authorised lifecycle:

1. The author freezes one clean exact Git candidate.
2. The STE lookup derives the review scope from the last accepted document
   identity and Git.
3. One independent Documentation Reviewer returns one complete `ACCEPT`,
   `APPROVED_WITH_EXACT_CORRECTIONS`, or `BLOCKED` verdict for the frozen scope.
4. For `APPROVED_WITH_EXACT_CORRECTIONS`, all exact replacement wording is in
   that review and is applied once against verified preimages.
5. One final deterministic validation runs after the review or correction.

Each new review result must use schema 2. It must record the complete blocker
set and confirm that the set is complete. `ACCEPT` and
`APPROVED_WITH_EXACT_CORRECTIONS` must have an empty blocker set. `BLOCKED` must
have a nonempty blocker set. Each blocker must bind its exact path, frozen
logical-unit identity, finding, and formal Issue 9 rule identifiers to the
frozen scope. The receipt must preserve the complete set and its exact candidate
and scope bindings. Validation must reject a `BLOCKED` result with no recorded
blocker.

The Documentation Review is the only linguistic conformance review. Do not run
a second Documentation Review. The final validation does not judge prose. It
must validate the official source identity, frozen candidate, Git-derived
scope, review result, receipt, expected document-level state, and final content.
It must reject unrelated post-review mutation.

Do not include an untouched legacy document in the review scope. Include the
complete document for the first material edit of an unreviewed legacy document.
After the document has an accepted identity, include only materially changed
complete logical units. Do not include unchanged previously accepted prose.
Keep accepted review state at document level; do not persist sentence,
paragraph, or logical-unit workflow state that Git can derive.

`tests/validate_agent_guidance.py` must give a `FAIL` result when a canonical
owner omits one of these controls. `tests/validate_governance_semantics.py` must
reject removal or weakening of a semantic control. Automatic validation and a
deterministic pre-check must not claim or change linguistic conformance.

`tests/validate_ste100_retrieval.py` must prove whole-document first review,
untouched legacy exclusion, later changed-unit scope, document-level durable
state, all three verdict routes, exact correction preimages, and final identity
binding. It must prove empty blocker sets for the two non-blocking verdicts. It
must also prove a nonempty complete blocker set for `BLOCKED`, exact finding and
frozen-unit binding, formal rule identifiers, and receipt preservation.
A `BLOCKED` result must produce no accepted-state proposal. The validator must
reject a missing, incomplete, empty, out-of-scope, or changed blocker set. The
final validator must reject source, scope, receipt, state, identity, or mutation
drift. A remaining linguistic, semantic, identity, or scope failure returns to
the owner.

[Technical provenance](PROVENANCE.md#asd-ste100-issue-9-reference) records the
rights state in a different authority boundary. The
[Technical Documentation Profile](ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
owns full applicability and the conformance review. The
[source and retrieval procedure](external/asd-ste100/README.md)
owns the STE lookup operation and the rebuild route.

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
their current structural/candidate facts. Within the analyser's bounded static
top-level call model, schema 2 separately checks callers of nominated roots,
callers crossing the proposed dependency closure and dependencies leaving that
closure. It does not execute either macro.

Fail-closed release-critical workflow coverage checks:

```bash
.venv/bin/python tests/validate_phase1_workflow_coverage.py
```

This cross-checks the 14 canonical Markdown inventory rows against their
machine-readable owners, oracle states, evidence/recipe/validator paths, gap
owners and future closure phases. It protects the exact B14/B15 source state
and requires successor-only blocked oracles to remain visible. Passing proves
coverage control, not that a partial or blocked workflow has received its later
GUI, migration, production, provenance or release authority.

Fail-closed railway terminology-assurance checks:

```bash
.venv/bin/python tests/validate_phase1_terminology.py
```

This validates the four assurance states, exact B14/B15 fingerprints and
known phrase counts, frozen ordinary-named evidence paths, open-review
ownership and future successor-product scan. It detects known terminology
drift and missing review control; it cannot determine contextual railway
correctness without the named human review.

Accepted Phase 1 closeout aggregation:

```bash
.venv/bin/python tests/validate_phase1_closeout.py
```

This reconciles the source fingerprints, workflow counts/gaps, selected pilot,
runtime and ingress policy, bounded performance defects, unmeasured target
slots, S1 manifest/lineage/oracle blocks, terminology reviews and the 10 owner
decisions in `PHASE1_CLOSEOUT.md`. It rejects loss of the accepted phase state,
broadened host support, invented performance evidence, waived later controls and
S1 clearance. Passing protects the 2026-07-22 acceptance; it does not broaden
the bounded Phase 2 authority.

Owner-accepted first-S1 package/evidence plan checks:

```bash
.venv/bin/python tests/validate_phase1_s1_pilot_plan.py
```

This protects all 15 S1 decision states and the recorded 2026-07-22 owner
acceptance, the exact B14/B15 source, the
structurally valid but `unknown` package manifest, blocked lineage scopes and
comparison-only Templot oracle. If a later chair schema exists, the validator
requires it to be attributed to the Phase 4 evidence and owner decision rather
than retroactively to Phase 1.
It fails closed if a designation, licence, dependency, rights status or
Templot artifact is promoted without evidence. Passing means the accepted
control is internally consistent, not that the package is project-cleared.

Project dashboard and current-record consistency:

```bash
.venv/bin/python tests/validate_project_progress.py
```

This enforces the compact project-plan sections and line budget, reconciles the
frozen Phase 5 closeout and accepted Phase 6 opening state with
`current/PHASE_EVIDENCE.md`, validates the detailed frozen/current risk and
decision JSON registers, protects the retired descriptive-path redirect and
checks the least-privilege, SHA-pinned standalone CI workflow. It does not
assess the quality of a decision's evidence, open a phase or replace
project-owner acceptance.

Fail-closed Phase 1 performance-boundary checks:

```bash
.venv/bin/python tests/validate_phase1_performance_boundaries.py
```

This verifies the exact B14/B15 and committed benchmark-report fingerprints,
nine declared legacy action profiles, all nested/harness relationships, the
per-run-before-median accounting rule, five `bounded-not-fixed`
instrumentation defects and four `not-implemented-unmeasured` target-pipeline
slots. It statically protects the current premature timing-write and late
solid-reuse source ordering, rejects double-counted children, invented budgets,
unsupported defect closure and fabricated target measurements, and does not
execute either macro or set a latency threshold.

Fail-closed Phase 1 candidate-boundary checks:

```bash
.venv/bin/python tests/validate_phase1_candidate_boundaries.py
```

This validates the five current candidate contracts against both complete
macro fingerprints, exact literal/function AST anchors and the live structural
inventory. It also derives the transition parameter order, station-data fields
and current chair settings/rail/timber/position/finding/support/result/signature
schemas from source. Inventory schema 2 freezes the bounded static closure-cut
counts; candidate-register schema 3 records the owner-accepted transition
selection and points to its exact pilot contract. Mutation checks prove that
source drift, a promoted chair status, a missing schema or a changed selection
fails closed. It does not import either macro, start extraction or approve
current chair data.

Selected transition-pilot contract and expanded parity grid:

```bash
.venv/bin/python tests/validate_phase1_transition_pilot.py
```

This verifies the exact B14/B15 fingerprints, three function signatures,
`GEOMETRY_TOLERANCE`, three external caller routes, zero outgoing project
dependencies, generated displacement/offset/solver grids, current error
diagnostics, B16/launcher identity, rollback rules and all declared evidence
paths. In its current state it requires the three mechanically identical
domain functions, exact B14/B15/modular value/type/error parity, the no-cache
A-B-A change-back cases, façade identity and no copied calculation body in the
B16 launcher. It
executes only the selected legacy function definitions for comparison; it does
not import or launch either legacy macro.

Phase 1 runtime and legacy ingress compatibility checks:

```bash
.venv/bin/python tests/validate_phase1_compatibility.py
.venv/bin/python tools/runtime_compatibility_probe.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tools/runtime_compatibility_probe.py --pass --require-qualified
```

The validator rejects a change to the exact B14/B15 fingerprints and
persisted-schema constants. It also rejects a change to the Addon metadata
intent, Python floor, host profiles, and B14/B15 ingress sets. It examines
selected migration boundaries without an import or launch of a legacy macro.
The test changes each compatibility class. It must reject each change that the
contract does not include.

The standalone probe must report `not-freecad-runtime`. The FreeCAD probe gives
evidence only when its `TRACKTEMPLATE_RUNTIME_PROBE=` record reports
`qualified`. The result must name one exact host profile:

- `linux-x86_64-flatpak-freecad-1.1.1`
- `linux-x86_64-flatpak-freecad-1.1.3`
- `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.

An exact 1.1.1 result does not qualify 1.1.3. An exact 1.1.3 result does not
qualify 1.1.2 or any other 1.1.x release. A result for one exact 1.1.3 profile
does not qualify the different exact 1.1.3 profile. The probe records no user
path.

D-GOV-006 adds only the exact FreeCAD 1.1.3 profile. All checks in the host
matrix gave the specified results in that runtime. The 1.1.1 evidence keeps its
recorded host identity. D-GOV-010 adds only the exact FreeCAD 1.1.3 profile with
CPython 3.13.13 and PySide6/Qt 6.11.1. The host matrix gave the specified
results in that runtime.

D-GOV-007 and D-GOV-010 define the
[hosts for Phase 6 performance evidence](PERFORMANCE_SOP.md#phase-6-performance-host-boundary).
Together, they authorise only the three profiles in the compatibility contract
to supply candidate evidence for Phase 6 performance. A subsequent decision can
admit only a performance result from one of these profiles.

The validator examines new schema-2 results. Each result and its summary must
record the ID and FreeCAD version of its exact host profile. One result set
must contain one exact host profile. To compare TrackTemplate performance, use
one exact host profile. A different method can compare host profiles only if
it independently shows the effect of the host profile and the TrackTemplate
effect.

If the project qualifies a subsequent host profile, this does not authorise
performance evidence from that profile. The validator rejects a new result
unless its ID/version pair is one of the three exact mappings. It rejects schema
1 and a `host_profile_id` value that is not a string. It rejects an exact-geometry
receipt that records a different FreeCAD version. It also rejects a result set
that contains two host profiles.

The 1.1.1 report from 2026-08-02 is a schema-1 report. It does not have a
`host_profile_id` field. It records FreeCAD 1.1.1, platform data, and the
qualified-runtime contract hash. These data identify the exact host profile
for FreeCAD 1.1.1. D-GOV-007 keeps that report as 1.1.1 evidence. The validator
does not change the report.

D-GOV-007 and D-GOV-010 admit no performance result. They define no value for a
performance budget. They do not accept Exit 4 or claim that performance became
better. Before the project claims that TrackTemplate performance changed on
this profile, the D-GOV-009 investigation must record a baseline for this profile.
The previous 1.1.1-only validator rejected the 1.1.3 test result. D-GOV-007
does not admit this test result as Exit 4 evidence.

The Phase 2 launcher uses the same evaluator through
`tracktemplate.bootstrap`. That launcher is not evidence for
document migration. Phase 4 accepted copied-target fixture evidence only for
`plain-line-spacing-matched-transition-intent`. For each new B14/B15 entity
family, the applicable phase must add its specified cases. A configuration JSON
migration is not evidence for an `.FCStd` file from a previous version.

Phase 1 licensing and manifest-control checks:

```bash
.venv/bin/python tests/validate_licensing_controls.py
.venv/bin/python tools/validate_dependency_manifest.py \
  reference/manifests/s1-chair-pilot.dependency-manifest.json
.venv/bin/python tests/validate_phase1_s1_lineage.py
.venv/bin/python tests/validate_phase1_other_snc_legacy_lineage.py
.venv/bin/python tests/validate_templot_s1_oracle.py
.venv/bin/python tests/validate_templot_s1_generation_map.py
```

The test checks the Draft 2020-12 schema vocabulary, package/output structural
rules, fail-closed `project-cleared` semantics, non-copyright-rights reviews,
contribution authority, duplicate identities and the current S1 control
record. The S1 record must validate truthfully as `unknown`; it is not expected
to pass the strict release gate yet.

The lineage test separately enforces the bounded first-S1/core register: both
scopes must remain blocked, every current entry containing unresolved Templot
reference data/media must remain `reference-only` without conflating that
status with GPL source-expression compliance. Unresolved evidence and owners
must be present, and all source anchors must match the immutable B14 and
accepted B15 files. When the
ignored local Templot archive is present it also verifies the archive and five
reviewed active member hashes; a clean checkout does not require that archive.

The other-S&C/legacy lineage test enforces the two remaining bounded scopes in
[`lineage/phase1-other-snc-legacy-lineage.json`](lineage/phase1-other-snc-legacy-lineage.json):
24 grouped dependencies retain their exact current `reference-only` or
`unknown` status, every anchor matches the immutable B14 and accepted B15
sources, and the two lineage files together cover all four audit-scope IDs.
When the ignored archive is present it verifies the five cited upstream member
hashes, including the explicitly inactive `chairs_unit_x.pas` evidence. It also
requires the current absence of other-S&C/legacy output dependency manifests;
adding one must be accompanied by a truthful register and validation update,
not an inferred positive status.

The oracle-contract test validates the blocked exact-556b capture
specification, local-only artifact rule, rejected-version guard and synthetic
DXF/STL semantics. When the ignored source ZIP is present it also verifies the
archive plus nine required members, the visible 556b revision evidence and
the four named S1 component routes through active `math_unit.pas`. It also
proves that the exact Lazarus project selects the non-`_x` math, pad, chair and
DXF units. It does not require an executable or raw Templot media in a clean
checkout and does not claim that the frozen oracle has been captured.

The generation-map test separately enforces the bounded code-1 source audit.
It protects the active/inactive project-unit distinction, exact source hashes,
unit conversions, coordinate frames, eight reference-only value groups, nine
generation stages, five constituent/base routes, manufacturing branches and
blocked acceptance gate. When the ignored ZIP is available it verifies every
mapped field and routine in its owning active unit, the complete code-1
constituent sequence and the DXF/STL emission functions. It does not approve
the mapped values, copy source expressions into production, or replace the
missing artifact and independent-evidence requirements.

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

Fast Phase 1 crossover preview/commit feasibility contract checks:

```bash
.venv/bin/python tests/validate_phase1_crossover_feasibility.py
```

This verifies the exact B14/B15 fingerprints and crossover AST parity, freezes
the current preview/late-complete-gate call ordering, validates both analytical
witnesses and fails closed if the successor zero-mutation rule is weakened. It
does not import FreeCAD or claim the mismatch is fixed. After reproducing the
ignored base fixture, exercise the read-only FreeCAD oracle with:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_crossover_feasibility.py
```

The oracle resolves both hosts by persisted identity, verifies the nine-object
semantic fixture, calculates both mapped turnout roads and the connector at
Host A chainages `500.000` and `746.298 mm`, creates no document objects and
requires the fixture bytes to remain unchanged. It must print
`Phase 1 crossover feasibility FreeCAD oracle passed`. The exact evidence and
remaining production/GUI acceptance decision is recorded in
[benchmarks/2026-07-21-b14-crossover-feasibility-characterisation.md](benchmarks/2026-07-21-b14-crossover-feasibility-characterisation.md).

Fast Phase 1 automatic-crossover-timbering contract checks:

```bash
.venv/bin/python tests/validate_phase1_crossover_timbering.py
```

This freezes the exact B14/B15 B4 source boundary after normalising B15's
recompute instrumentation, the controlled result/signatures and the distinction
between accepted semantics and three current defects. Exercise the copied-
fixture lifecycle in real FreeCAD with:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_crossover_timbering.py
```

The oracle creates `XO-001` only in a temporary copy, applies and reuses B4,
checks exact Undo/Redo and save/reopen, distinguishes display-only from
calculation-input invalidation, clears B4 and injects the first tagging failure.
It must print `Phase 1 crossover timbering FreeCAD oracle passed` and leave the
source fixture byte-identical. The retained untagged object, display-only
rebuild and nested diagnostic drift are required defect witnesses, not future
behaviour. Exact evidence and remaining scope are in
[benchmarks/2026-07-21-b14-crossover-timbering-characterisation.md](benchmarks/2026-07-21-b14-crossover-timbering-characterisation.md).

Fast Phase 1 chair-analysis persistence/reuse contract checks:

```bash
.venv/bin/python tests/validate_phase1_chair_analysis_persistence.py
```

This freezes the inherited B14/B15 logical-analysis source boundary, fixed
`XO-001` semantic/display digests, timing-persistence ordering, effective-
status scan and active panel refresh route. Exercise cold calculation,
unchanged reuse, reuse Undo/Redo and save/reopen in real FreeCAD with:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_chair_analysis_persistence.py
```

It must print `Phase 1 chair analysis persistence FreeCAD oracle passed` and
leave the ignored fixture byte-identical. Truncated persisted timings, metadata
and history mutation on a cache hit, repeated status scans and redundant panel
refresh are required defect witnesses, not accepted successor behaviour. Exact
evidence and remaining scope are in
[benchmarks/2026-07-21-b14-chair-analysis-persistence-characterisation.md](benchmarks/2026-07-21-b14-chair-analysis-persistence-characterisation.md).

Fast Phase 1 chair-analysis invalidation/presentation contract checks:

```bash
.venv/bin/python tests/validate_phase1_chair_analysis_invalidation.py
```

This classifies every normalised setting and every emitted rail/timber field
for the fixed post-B4 `XO-001`, freezes representative logical-output
mutations and guards the source precision/order boundary. Exercise the actual
application cache and headless diagnostic-layer topology in real FreeCAD with:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_chair_analysis_invalidation.py
```

It must print `Phase 1 chair analysis invalidation FreeCAD oracle passed` and
leave the ignored fixture byte-identical. The stale cache hit, five-decimal
precision alias, record-order over-invalidation, downstream-setting
over-invalidation and exact-Part presentation rebuild are required legacy
defect witnesses, not successor behavior. FreeCADCmd visibility is explicitly
non-authoritative; real-GUI visibility, selection, history and refresh remain
open. Exact evidence and scope are in
[benchmarks/2026-07-21-b14-chair-analysis-invalidation-characterisation.md](benchmarks/2026-07-21-b14-chair-analysis-invalidation-characterisation.md).

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

The controlled B14 runs and export source/transaction audits expose seven
behaviours that need focused tests with their eventual production fixes.
Do not encode the current defect as the expected result merely to increase the
test count.

The first four performance items below, together with repeated status scans,
are explicitly bounded in
[`contracts/phase1-performance-boundaries.json`](contracts/phase1-performance-boundaries.json).
That makes unsafe current measurements ineligible for optimisation selection;
it does not mark any defect fixed or replace the regression obligations.

1. Crossover preview/commit feasibility: the fail-closed Phase 1 contract and
   read-only FreeCAD oracle now freeze B14's `500.000 mm` preview-pass/complete-
   fail witness and its valid `746.298 mm` control. The successor regression
   must use the same persisted host identities and request for preview and
   create/edit/extend; cover both mapped turnout roads and the connector; reject
   the lower witness before Part construction or document/history mutation;
   accept the documented witness; and prove later exact-build agreement. The
   characterisation does not mark that implementation fixed.
2. Chair timing persistence: the focused fixed-`XO-001` contract now proves
   that cold and reused persisted `performance_timings_ms` omit metadata,
   diagnostic display, recompute, commit and total work, and that unchanged
   reuse rewrites the result in a new Undo entry. Preserve that defect witness;
   the successor must persist the final complete payload after all claimed
   work, reconcile it with the enclosing stage and perform no document/history
   mutation for a current unchanged result.
3. Effective-status reuse: the same contract now freezes the independent rail,
   timber and signature scan on every chair-status query. Query chair/support/
   layout/solid status through one shared snapshot or demonstrably bounded
   signature reuse, assert unchanged results are equivalent, then mutate each
   relevant input class and verify correct invalidation.
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
7. Automatic crossover timbering lifecycle: the fixed Phase 1 oracle preserves
   B14's characterised `XO-001` records, calculation-input invalidation, reuse,
   history and persistence, but diagnoses three behaviours that must not be
   migrated. Persist one canonical returned/reused analysis payload; exclude
   display controls from resolution signatures and solver/geometry/history
   work; and make every injected failure restore the exact document and history
   without retaining an untagged partial object. Extend invalidation through
   every engineering-input class before retiring the legacy path.

## Future validation assets

Before retiring a legacy path, add representative, non-sensitive fixtures or deterministic input recipes covering:

- curve/easement and multi-track generation;
- turnout creation and editing;
- straight- and curved-host crossovers;
- wider automatic timbering and chair analysis (the fixed `XO-001` B4 and
  post-B4 logical-analysis lifecycles now have dedicated oracles);
- an exact local capture produced under the tracked frozen-Templot-S1
  constituent/assembly recipe (the recipe/validator exists; the exact 556b
  executable, fixture and artifacts remain blocked);
- a versioned native S1 chair-definition package with invalid/corrupt fixtures;
- one non-sensitive, project-cleared calibrated scan/CAD/measurement fixture for
  the assisted S1 assimilation pilot;
- lightweight preview selection/editing;
- exact validation and each production export family;
- failure rollback and document reopen.
