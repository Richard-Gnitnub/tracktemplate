# Validation Strategy

## Purpose

Validation protects railway correctness while the macro is optimised and
separated into architectural layers. Tests must distinguish analytical
correctness, FreeCAD integration, display behaviour and production output.
[TESTING_POLICY.md](TESTING_POLICY.md) defines the project-wide obligation to
add tests and the limited circumstances in which an existing test oracle may
change.

<a id="document-boundary"></a>

## Validation-document responsibility

This document owns durable validation layers and evidence-interpretation
rules. It also owns stable runner profiles, entry points, and the minimum
change matrix. Change it only when one of these owned contracts changes.

A new test, completed run, performance result, or current-phase proof does not by
itself justify changing this document. Put executable detail in the affected
test or runner, evidence required by the
[Level 2 or Level 3 documentation lifecycle](ENGINEERING_POLICY.md#documentation-lifecycle)
in [current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md). Put measurement
results for a bounded scope in a dated report under `reference/benchmarks/`.
Do not use this document as a tranche log.

The existing detailed command catalogue remains pending a separate bounded
simplification because it contains retained validation obligations. This
document responsibility controls new changes. It does not authorise more
per-tranche additions.

## Current version roles

- `AdvancedTurnout.FCMacro` is the immutable B14 legacy comparison oracle (`10.2A8A7B14`).
- `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro`
  is the accepted B15 behavioural reference. It entered Phase 1 as
  `10.2A8A7B15`.
- `10.2A8A7B16` identifies the current modular development checkpoint. Its
  small `TrackTemplate.FCMacro` composition root routes three transition
  functions exclusively through the modular domain. The inherited B15 GUI
  host remains a lazy compatibility dependency. Dual-route comparison is
  development-only oracle tooling. This is not the public Workbench/RC
  version.
- `tests/validate_b15.py` validates B15 structure and analysis. It compares
  selected railway functions and proves complete inherited-module AST parity
  with B14. Normalisation applies only to version, launch, docstring, and
  recompute-instrumentation differences.
- `tests/freecad_validate_b15.py` exercises the B15 chair display path in real headless FreeCAD.
- `reference/contracts/phase1-compatibility.json` defines the currently
  qualified FreeCAD stack and standalone Python floor. It also defines bounded
  B14/B15 future migration ingress. It is a Phase 1 control. It is not an
  implemented migrator or final Addon manifest.

B15 passed the real-GUI, reuse, solid-equivalence, and save/reopen
qualification for the bounded scope recorded in
[benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md](benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md).
The project owner accepted that evidence and the formal version roles on
2026-07-19. Acceptance applies only to the declared B15 delta. B14 remains
available as the immutable legacy oracle for each Phase 1 characterisation
slice and later parity check.

These roles are current project state, not a permanent versioning scheme.
Update this document when the oracle/reference relationship changes.

## Validation layers

### 1. Source and structural validation

- Parse every changed macro as Python.
- Check version assignments and launch limits.
- Prevent accidental whole-file rewrites or unrelated changes.
- Verify required function, schema and workflow structure.
- For the legacy macros, run the Phase 1 structural inventory/validator.
  Detect drift in duplicate definitions, captured aliases, import-time method
  patches, mutable-state signals, and selected caller/dependency closures.
- For retained source-organisation changes, review the named authoritative
  implementation and each genuinely shared invariant. Review the narrow
  interface, dependency direction, and each temporary duplicate or retirement
  condition.
- `tests/validate_phase2_foundation.py` and `tools/modular_structure.py` fail
  on a forbidden domain/platform import, undeclared or prohibited layer edge,
  circular dependency, speculative module or import-time structural warning.
  Retain and extend these guards with every applicable package change.
- Treat structural metrics as risk signals, not proof of maintainability.
  Railway-semantic cohesion and abstraction quality still require review and
  behavioural evidence.

### 2. Analytical validation

- Exercise pure calculations without depending on a FreeCAD GUI.
- Compare geometry records, topology, timbers, chairs, findings, stable
  identities, and deterministic ordering.
- Test cache misses, valid reuse, and invalidation after each relevant input
  class changes.

### 3. FreeCAD document validation

- Use an exact host profile that the Phase 1 compatibility contract qualifies.
  The contract qualifies two exact Linux x86_64 stable
  `org.freecad.FreeCAD` Flatpak profiles. They use FreeCAD 1.1.1 and 1.1.3.
  Both profiles contain CPython 3.13.14, PySide6/Qt 6.10.3,
  OpenCASCADE 7.8.1, and Coin 4.0.8. FreeCAD 1.1.2 and all other host profiles
  are not qualified.
- Make sure that object types, properties, groups, visibility, transactions,
  recomputes, and cleanup are correct.
- Make sure that save and reopen behaviour is correct when persistence changes.
- Make sure that transient validation or export objects do not stay in the
  editable document.

### 4. Presentation validation

- Exercise the affected view in the GUI.
- Check visual alignment, style layers, visibility, selection-to-domain
  identity mapping, and edit handles.
- Verify parameter edits, undo/redo, document close/reopen, and cache
  invalidation.
- Treat the preview as display evidence only, never exact production validation.

### 5. Exact geometry and export validation

- Compare legacy and replacement bounds, lengths, profiles, topology and solid validity.
- Verify scale and planarity for SVG/DXF outputs.
- Verify valid solids/meshes for STEP/STL outputs.
- Compare filenames, categories, record IDs and manifest rows deterministically.
- Exercise staging, overwrite handling, failure rollback and transient-object cleanup.
- For procedural chairs, compare named constituents and full-size dimensions
  with the accepted reference. Compare profiles, cross-sections, datums, rail
  interfaces, topology, and assembled placement. FreeCAD B-rep and Templot
  DXF/STL tessellations need not have identical bytes or face order. The
  agreed geometric oracle must prove equivalence.

### 6. Chair-definition and assimilation validation

Chair work has an additional validation limit. The accepted production
requirement deliberately exceeds the B15 five-box S1/S1J body. B15 remains the
behavioural reference for its declared analysis, representation, persistence,
and cache delta. Its rectangular body is gap evidence, not the future exact
chair oracle.

Before a chair definition or generator is accepted:

- Parse and validate the definition without FreeCAD/Qt. Prove a deterministic
  serialise/load/serialise round-trip. Prove stable definition and component
  identities.
- Reject missing required units, frames, datums, components, provenance,
  package versions, or rail-interface data. Reject unsupported future versions
  without partial geometry generation.
- Prove that prototype source values and geometry are separate from model
  scale, rail-fit policy, and manufacturing compensation. Use complete
  signatures and invalidation for each input class.
- Generate each named constituent in the bounded scope through the common
  procedural builder. Assemble reusable prototypes with deterministic
  transforms. Regenerate without the source scan/CAD file or retained FreeCAD
  shapes.
- Compare the native S1 definition with the frozen Templot
  component/assembly oracle. Use agreed dimensional, section/profile,
  surface-distance, interface, bounds, topology, and solid-validity metrics.
- Prove rail fit, clearances, keys or loose components, and applicable
  fastening or plug interfaces independently of visual plausibility.
- Verify that lightweight 2D symbols remain derived from the same accepted
  definition. Do not construct production solids during routine editing.
- After exact validation, compare deterministic STL/STEP and retained-component
  outputs. Include separate-part identities and assembly placement.

For the assisted S1 assimilation pilot, also validate calibration, units, and
the coordinate frame. Validate operator-declared components and landmarks.
Compare measured values with inferred values. Validate unresolved findings,
provenance, file hashes, and reported regenerated-versus-source residuals.
Acceptance requires recorded tolerances and explicit operator approval. A low
residual does not by itself validate hidden, worn, or nominal geometry.

Raw tessellation hash equality is not a general geometric oracle. Meshing
settings and face ordering can change without changing the solid. Preserve
source hashes for provenance. Then compare regenerated geometry with
format-appropriate semantic metrics.

### 7. Performance validation

- Follow [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md).
- Report both editing cost and deferred Validate/Export cost.
- Prove that an optimisation did not increase speed by changing results or the
  bounded scope for validation.

## Verified commands and CI

Run from the repository root.

<a id="developer-tool-boundary"></a>

### Development-toolchain preflight

This section is the human-readable owner for the development-toolchain
preflight. The machine declaration is
[`development-toolchain-v1.json`](contracts/development-toolchain-v1.json).
The declaration gives the type of each tool and the workflow operations for
which it is necessary. It also names each supported fallback and its project authority.

`requirements-dev.txt` contains exact pins for necessary Python development
packages. These packages are not Addon dependencies. Ruff is a repository
validation package. Click is a conditional dependency of the real-GUI
development bridge. The project virtual environment and the qualified FreeCAD
profiles have separate package controls.

Before the dependent workflow operation, use the applicable command:

```bash
.venv/bin/python tools/development_toolchain_preflight.py --stage development
.venv/bin/python tools/development_toolchain_preflight.py --stage validation --run-ruff
.venv/bin/python tools/development_toolchain_preflight.py --stage documentation
.venv/bin/python tools/development_toolchain_preflight.py --stage freecad
.venv/bin/python tools/development_toolchain_preflight.py --stage freecad-gui
.venv/bin/python tools/development_toolchain_preflight.py --stage publication
```

The development-toolchain preflight has these requirements for each operation:

| Operation | Required result |
| --- | --- |
| `development` | Git must identify this repository. The project `.venv` must contain CPython at the development floor in the compatibility contract. |
| `validation` | The checks of the `development` requirements must give a PASS result. The checks of the exact declarations for Python packages, Ruff version, and Ruff configuration must give a PASS result. With `--run-ruff`, the tool then does the fixed repository check. This check changes no file. |
| `documentation` | The checks of the local official STE source and derived cache must give a PASS result. The file owner and file mode checks for `pdftotext` must give a PASS result. One live extraction from the source must give a PASS result. |
| `freecad` | Flatpak must start the existing runtime probe. The probe must return one exact profile that the compatibility contract qualifies. |
| `freecad-gui` | The checks of the `freecad` requirements must give a PASS result. The checks of the exact Click declaration and system version must give a PASS result. The checks of the necessary shell tools, pinned bridge commit, reviewed tree, and test set must give a PASS result. |
| `publication` | Git and GitHub CLI must identify the expected repository. The checks of GitHub authentication, default branch, and write access must give a PASS result. |

The development-toolchain preflight examines only the selected operation. A
missing tool gives a `FAIL` result before the dependent operation. The
development-toolchain preflight does not install a package or get a source
file. It does not change authentication data or a host.

Ruff version `0.16.4` and `ruff.toml` define the repository Ruff contract.
Ruff uses Python 3.12 syntax and the selected `E9`, `F63`, `F7`, and `F82`
checks. It does not use a cache or change a file. The fixed exclusion preserves
the immutable B14 and B15 comparison sources. One injected-global probe has a
bounded `F821` exception.

The preferred Ruff executable is `.venv/bin/ruff`. If that path is absent, the
supported fallback is a Ruff executable on the user `PATH` with the exact
necessary version. The development-toolchain preflight examines its file owner,
file mode, path, version, and configuration. If the preferred executable has
a wrong version, the development-toolchain preflight does not use the supported
fallback. A tool manager for the user can supply this executable. This manager
has no responsibility for TrackTemplate packages.

All other declared tools have no supported fallback. The official ASD/STEMG
web source stays an alternative source for the independent Documentation
Reviewer. It does not satisfy authoring requirements for local
extraction. The qualified FreeCAD profiles are exact alternatives in the
existing compatibility contract. Other versions do not have this qualification.

Do not use `uv init` in this repository. Do not add a root `uv.lock`. A package
manager migration is a different authorised task.

### Programmatic regression pipeline

Use the local pipeline as the usual concise entry point for regression tests:

```bash
.venv/bin/python tools/run_regression_pipeline.py
.venv/bin/python tools/run_regression_pipeline.py --profile transition
.venv/bin/python tools/run_regression_pipeline.py --profile transition-gui
```

The default `standalone` profile first uses the development-toolchain preflight
for `validation` and Ruff. It then checks each tracked Python and macro source
with `ast.parse`. It does the complete standalone matrix for a clean
checkout. Before its qualified headless checks, the `transition` profile uses
the development-toolchain preflight for `freecad`.

Before its isolated ViewProvider workflow, the explicit `transition-gui`
profile also uses the development-toolchain preflight for `freecad-gui`.
Profile names describe continuing behaviour, not phase acceptance. Test paths
with a phase prefix can change names when their product boundary is stable.
This does not end the test contract.

Each step must give a zero exit status and its documented success sentinel. Raw
output stays in ignored `benchmark-output/validation-pipeline/` run
directories. The terminal gives only step results and
`TRACKTEMPLATE_REGRESSION_PIPELINE=`. If a necessary check gives a FAIL result, the pipeline
stops before later layers with a higher cost. The standalone runner still
completes each standalone validator. Thus, one log shows all observed
failures.

The qualified and GUI profiles are workstation evidence, not clean-checkout
CI. The GUI profile stays explicit. It does not establish screenshot hashes,
numerical timing gates, or a mandatory GUI-host workflow.

The tracked [standalone CI workflow](../.github/workflows/ci.yml) starts on
pushes to `main` and pull requests. It examines each tracked Python and macro
source with `ast.parse`.
Then it does each `tests/validate_*.py` check through the complete-run
standalone runner. The runner continues after a failed validator. Its
structured summary shows all observed failures from one run.

Use the same explicit profiles locally:

```bash
.venv/bin/python tools/run_standalone_validators.py --profile ci
.venv/bin/python tools/run_standalone_validators.py --profile local
```

The `ci` profile proves deterministic tracked contracts in a clean checkout.
It shows that the runner fails closed when an ignored critical asset is missing. It does not
claim that the asset is available. The `local` profile also has a requirement for
workstation-only archive, hash, branch, and upstream evidence. Neither profile
replaces selected FreeCAD, GUI, backup/restore, output, or owner-decision
evidence.

For diagnosis of a Python source error, use the same local source check:

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

This standalone standard-library validator examines the supporting JSON-LD/OWL
projection and its Markdown reference. It does not replace the canonical
architecture or schema validators. It also does not replace railway tests,
FreeCAD integration evidence, or current phase and authority records.

Current Phase 3 transition routing and rollback product boundary:

```bash
.venv/bin/python tests/validate_phase3_transition_routing.py
```

This standard-library check does the complete synthetic legacy and modular
routes. It also does the legacy change-back route. It covers fail-closed
source, contract, API, and launch-limit cases. The compatibility adapter must
stay in the declared dependency layer without structural warnings.

Phase 3 routed full-workflow harness contracts:

```bash
.venv/bin/python tests/validate_phase3_transition_workflows.py
.venv/bin/python tests/validate_phase3_transition_performance.py
```

The first command protects the reusable driver seam and exact B14/B15
fingerprints. It also protects the B16 route loader, four-process controller,
and five-field volatile-data limit. It protects scenario order, preference
restoration, bounded B14-to-B15 generator-version handling, and exact semantic
comparison. The second protects the 202-case calculation product boundary. It
also protects profiled action selection, repetition/order rules, descriptive
comparisons, and committed evidence links. Neither command starts FreeCAD.

Accepted Phase 2 FreeCAD loading and zero-document-mutation smoke:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase2_foundation.py
```

The standalone validator also starts an isolated interpreter. It blocks
FreeCAD, Part, Qt, and pivy imports. The Phase 2 FreeCAD smoke must print
`Phase 2 FreeCAD foundation smoke test passed`. It loads the launcher
definitions. It does not start the current orchestration entry point. Then it
examines package/API/domain resolution, exact runtime qualification, and zero
document mutation. The accepted loading check stays independent of later
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

The Phase 3 standalone test keeps legacy → modular → legacy comparison only
through `tools.phase3_transition_pilot`. The Phase 4 retirement validator
has a requirement that the oracle stays outside the product package. It removes the
route argument and legacy exports from current composition. It proves that the
modular-only host loader is a clean, lazy compatibility dependency.

The FreeCAD test does the current B16 default operation. It must not load the 2.3 MB
B15 host or mutate a document. It rejects the retired legacy argument before
host loading. It shows the accepted all-caller parity through the
development-only oracle.

Then it loads a separate product session. All three
bindings must use the modular API without a comparison route. It must print
`Phase 3 transition routing FreeCAD smoke test passed`. This smoke starts no
operator dialog.

The immutable B14/B15 workflow evidence stays the accepted
GUI oracle. Do not rewrite the independent Phase 2 loading smoke.

Phase 4 transition canonical-state foundation:

```bash
.venv/bin/python tests/validate_phase4_transition_state.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_transition_state.py
```

The standard-library validator owns the accepted schema-v1 deterministic
round-trip for bounded reads. It owns complete transition-analysis signatures,
cold/reuse/change-back, label-only reuse, and numerical invalidation. It also
owns stable identity, stale or corrupt derived-result recovery, and fail-closed
input cases. The product boundary for application dependencies is also part of
this contract.

The qualified-FreeCAD smoke proves only runtime/type
compatibility.
It proves the same exact JSON round-trip and zero document mutation. It does
not prove FreeCAD properties, transactions, Undo/Redo, or FCStd save/reopen.

Phase 4 qualified FreeCAD transition persistence:

```bash
.venv/bin/python tests/validate_phase4_transition_persistence.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_transition_persistence.py
```

The standalone check protects the concrete-adapter dependency direction and
property/type contract. It also protects the qualified-write product boundary
and the bounded scope of the disposable fixture. It does not import FreeCAD.

The FreeCAD test uses only newly created disposable documents and a temporary
FCStd. It proves exact canonical save/reopen and stable identity independent
of name, label, or order. It proves one-command create/update history and
create/update Undo/Redo. It covers no-op history, preflight rejection, and
injected post-write rollback.

It also covers stale or corrupt derived results,
foreign-object preservation, and rejection of unqualified runtime evidence.
Its success sentinel is
`Phase 4 transition FreeCAD persistence validation passed`.

Phase 4 B14/B15 legacy-document detection:

```bash
.venv/bin/python tests/validate_phase4_legacy_document_detection.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_legacy_document_detection.py
```

The standalone matrix proves deterministic B14-only, B15-only, and accepted
mixed-window reporting. It proves foreign-object exclusion and
inspection-only results for versionless or future data. Malformed or
conflicting data must fail closed. The matrix also proves exact contract
gating, isolated import, and zero outer-detector write authority.

The FreeCAD
test uses only newly created disposable documents and a temporary FCStd. It
proves zero mutation during inspection. It also proves an identical mixed
report after save, close, and reopen. Its success sentinel is
`Phase 4 legacy document FreeCAD detection validation passed`. This is only
outer-ingress evidence.

The detector stays inspection-only when one exact
family is separately qualified. It cannot advertise a complete document as a
supported migration source.

Phase 4 read-only plain-line transition family assessment:

```bash
.venv/bin/python tests/validate_phase4_plain_line_transition_assessment.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_plain_line_transition_assessment.py
```

The standalone matrix consumes the accepted outer detector. It proves exact
B14, B15, and expected-mixed handling for the spacing-matched secondary
plain-line transition slice. Its contract makes complete typed settings necessary. Stable
identities come from template-set identity, persisted semantic track ordinal,
and end.

The matrix replays the canonical solver exactly. It rejects partial,
unsupported, corrupt, or ambiguous input. It keeps zero write, migration,
or production authority.

The FreeCAD check opens the reproducible ignored B14
base fixture as read-only. It gets the two exact canonical candidates and
compares document, property, and history snapshots. The source FCStd hash must
stay unchanged.

Its sentinel is
`Phase 4 plain-line transition FreeCAD assessment passed`. This read-only
assessment does not authorise a copied-target write or advertise family
support. The registry and fixture below own those separate controls.

Exact-family Phase 4 copied-target transition migration fixture:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_plain_line_transition_migration.py
```

This isolated fixture starts B14, B15-only, and expected mixed targets as
physical copies of disposable source FCStd files. The host-independent
operation has a requirement for exact family-level source and target assessments. Then it
uses the injected qualified FreeCAD writer one time. The writer creates both
canonical transition records in one batch transaction.

The fixture must show
one-step Undo/Redo and duplicate preflight with no history. It must show exact
canonical and legacy persistence through target save/reopen. It must also show
source-byte preservation and complete abort after an injected second-payload
failure. The original reproduced B14 fixture hash must stay unchanged.

`SUPPORTED_MIGRATION_FAMILIES` must contain exactly
`plain-line-spacing-matched-transition-intent`. Migration support must be true
only for that family. Production-output authority must stay false. Its
sentinel is
`Phase 4 copied-target transition migration fixture passed`. A PASS result from this test
proves the exact contract for the fixture-only family. It does not qualify a
complete document or authorise a Workbench/operator migration path.

Use the same persistence and rollback fixture in an isolated real-GUI process.
This command also examines the GUI host boundary:

```bash
tools/freecad_bridge/run-isolated \
  tools/freecad_bridge/freecad-cli execute-code \
  'assert __import__("FreeCAD").GuiUp; import runpy; runpy.run_path("tests/freecad_validate_phase4_plain_line_transition_migration.py", run_name="__main__")'
```

Use `runpy.run_path` instead of `execute-code --file` for this validator. The
latter bridge mode does not define `__file__`. A successful JSON bridge
response must contain the same fixture sentinel. This is real-GUI host,
document-lifecycle, persistence, and rollback evidence for the exact supported
fixture-only family. It is not evidence of an operator-visible command,
target-path control, or production output.

Phase 4 neutral chair-definition package:

```bash
.venv/bin/python tests/validate_phase4_chair_definition.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_chair_definition.py
```

The standalone validator owns chair-package schema v1 and the explicitly
non-prototype synthetic fixture. It owns the deterministic signed round-trip,
exact source quantities, canonical decimal quantities, and unit conversion.
It also owns the fixed chair-local frame and all datum, component, procedure,
and rail-interface references.

The validator also covers manufacturing separation, lineage coverage,
acceptance, and external dependency-manifest linkage. The
missing, corrupt, unsupported, and ambiguous cases form the failure matrix.
The existing strict project-clearance
validator must give a PASS result for the synthetic manifest. The test then proves that Phase 9 production admission blocks
geometry, document, and filesystem mutation.

The qualified-FreeCAD test proves
only bundled-Python compatibility. It proves the same exact package round-trip
and zero document mutation. Its sentinel is
`Phase 4 chair-definition FreeCAD compatibility validation passed`. Neither
test supplies an S1 definition, starts a chair builder, or qualifies output.

Current Phase 3 real-GUI workflow parity:

```bash
tools/freecad_bridge/run-phase3-transition-workflows \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

This does plain-line editing and connected-straight lifecycle automation. Four
fresh isolated GUI processes use the complete legacy and modular routes. The
test must show exact route-independent workflow contracts and preserved route
bindings. It must also show undo/redo, save/reopen, isolated preference
restoration, and source non-mutation. It covers the plain-line invalid-input
and transaction-abort recovery paths.

It records raw timing observations. It
is not the contracted calculation or workflow performance profile.

Current Phase 3 contracted performance profile:

```bash
.venv/bin/python tools/phase3_transition_performance.py \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

This does nine same-process repetitions per route for the calculation grid.
The complete grid is frozen and has 202 cases. Then it does three repetitions
per workflow and route in separate new FreeCAD GUI processes. It alternates route order and keeps exact
workflow parity. It records medians, ranges, CPU, end-minus-start RSS, and
object deltas.

The 12-process GUI profile is checkpoint evidence, not a fast
test. Its timings do not establish an interaction budget or an optimisation
claim. Raw paths, FCStd files, and JSON stay ignored. A sanitised committed
performance report stays under `reference/benchmarks/`.

Retained Phase 5 bounded Coin resource profile:

```bash
.venv/bin/python tests/validate_phase5_transition_coin_resource_profile.py
.venv/bin/python tools/phase5_transition_coin_resource_profile.py
```

The fast standard-library validator protects the fixed 32-object fixture and
the three-process minimum. It protects cold and warm measurement fields,
stable identity, and scene counts. It also protects cache reuse, zero-`Shape`,
and cleanup contracts. It does not import FreeCAD.

The profiler starts three new
FreeCAD GUI processes. Each process is isolated and qualified. Each process constructs 32 logical
objects and preview layers. It does one untimed warm-up and three measured
unchanged refreshes. It records wall time, process CPU, explicit recompute
duration, and end-minus-start RSS. It also records actual Coin-layer counts,
active-node counts, and individual samples.

Correctness invariants are gates.
Timings stay descriptive and establish no representative workload, capacity,
or numerical budget. Raw JSON and logs stay ignored. The sanitised result
and limitations are in
[benchmarks/2026-07-29-phase5-transition-coin-resource-profile.md](benchmarks/2026-07-29-phase5-transition-coin-resource-profile.md).

Retained Phase 5 bounded transition interaction/resource range profile:

```bash
.venv/bin/python tests/validate_phase5_transition_interaction_range_profile.py
.venv/bin/python tools/phase5_transition_interaction_range_profile.py
```

The fast standard-library validator protects five declared scale points and a
three-fresh-process minimum. It protects host-independent result validation.
It also protects exact object, layer, node, mapping, edit-isolation, Undo, and
cleanup invariants. The explicit non-acceptance condition stays. The
validator imports neither FreeCAD nor Qt.

The profiler repeats the qualified
Entry/Exit family unit at 1, 2, 4, 8, and 16 sets. This gives 2–32 logical
objects. A test-only view grid makes repeated local-frame previews separately
hittable. It does not change canonical state or product placement.

At each scale, three new qualified GUI processes start in isolation. Each process
does one real Qt pointer selection and opens the transient parameter
editor. It enters one length through real keyboard and button input. It
examines one selected-only edit and one Undo. Then it removes each cache and
proxy, and closes each document.

It records cold, selection, dialog, edit, Undo, and
cleanup measurements. Each measurement includes wall time, CPU, and
end-minus-start RSS. Correctness invariants are gates. Values stay
descriptive and accept no capacity, interaction budget, renderer, or
optimisation. The sanitised method, observations, and limitations are in
[benchmarks/2026-07-31-phase5-transition-interaction-range-profile.md](benchmarks/2026-07-31-phase5-transition-interaction-range-profile.md).

Retained Phase 5 representative Entry/Exit multi-object editing workload:

```bash
.venv/bin/python tests/validate_phase5_transition_parameter_editor.py
.venv/bin/python tests/validate_phase5_transition_multi_object_edit.py
tools/freecad_bridge/run-phase5-transition-viewprovider
```

The standalone parameter-editor validator proves the internal length command
and fail-closed selection controller. It also proves the accepted UI
dependency direction. It imports neither Qt nor FreeCAD. The multi-object
validator fixes the workload rationale. It protects the real-GUI proof and
runner.

The representative product boundary is the smallest plain-line transition
family with complete qualification. One secondary track produces one canonical Entry
record and one canonical Exit record. Distinct deterministic transition
lengths make the two development previews pointer-disambiguable. They are not
product defaults.

The existing isolated ViewProvider runner first keeps the one-object
lifecycle and save/reopen proof. Then it does the two-object workload in
the same qualified real-GUI process. The process starts from a new empty
document.

A real Qt mouse click must select the red Exit preview. It must
resolve the stable domain identity. A modeless dialog must have the FreeCAD
main window as its parent. It must show that identity and the current
transition length.

Real Qt keyboard input and an Apply-button click must route
one length edit through the internal application command. Undo, Redo, an
injected refresh failure, and a cleared-selection attempt must have only the
intended results. The Entry state and cache must stay untouched. If the operator applies the
unchanged displayed value, the operation must make no history.

The failure must stay
visibly diagnostic. The no-selection attempt must change neither state,
history, nor cache counters. Selected and edited dialog captures stay for
visual inspection.

Each state must keep two compact `App::FeaturePython`
objects and two Coin layers. It must keep 14 active selectable-scene nodes,
zero `Shape` properties, and identical stable selection mappings. The runner
must get the inner
`TRACKTEMPLATE_PHASE5_MULTI_OBJECT_EDIT_GUI=` result and give the existing
outer `TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=` sentinel.

This workload represents only the currently qualified fixture-only family
shape. It does not establish whole-layout capacity or an interaction budget.
It also does not establish automatic product loading, menu wiring, renderer
suitability, or owner acceptance.

Retained Phase 5 post-open attachment and explicit B16 lifecycle product boundaries:

```bash
.venv/bin/python tests/validate_phase4_transition_persistence.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase4_transition_persistence.py
.venv/bin/python tests/validate_phase5_transition_coin_viewprovider.py
.venv/bin/python tests/validate_phase5_transition_editing_lifecycle.py
tools/freecad_bridge/run-phase5-transition-viewprovider
```

The persistence checks protect and use the read-only
`read_transition_objects(document)` adapter operation. Qualified FreeCAD must
ignore foreign records and validate each canonical transition record. It must
reject duplicate stable identities. It must return `(object, state)` pairs in
transition-ID order. It must change no property or Undo/Redo state.

The ViewProvider checks cover the explicitly invoked
`TransitionCoinDocumentAttachmentFixture`. The host-independent proof uses two
records supplied out of order. It refreshes only one retained cache. On
disposal, it restores both original default proxies. After an injected
second-object attach failure, it clears each live binding and cache.

The
isolated real-GUI proof saves and reopens one canonical record. It shows
that the document kept no transient attachment marker. It injects and recovers from a
Coin attach failure.

Then it starts document attachment one time. The proof
must show a new cache and ViewProvider with an equivalent preview. It must show
a no-op refresh with cache reuse and visible rendering. Disposal must clear derived
state and restore the host proxy.

Canonical JSON, property lists, object count,
and history must stay unchanged.

The same runner then proves the saved/reopened representative Entry/Exit
attachment product boundary. First, it removes the two manual editing
fixtures and caches. It saves only the two canonical `App::FeaturePython`
records. It closes and reopens the FCStd. Then it starts document attachment
explicitly.

The attachment must enumerate Entry then Exit by stable identity.
It must rebuild two new equivalent caches and Coin layers. It must preserve
both pre-save selection mappings. It deliberately discards Entry's cache as an
observable sibling trap. An unchanged Exit refresh must then reuse its cache.

Entry's cache must stay missing. Its bound source signature, selection root,
and mapping must stay unchanged. The attachment must keep two objects, two
logical layers, and 14 active selectable-scene nodes.

It must keep zero
`Shape` properties and have zero attachment history delta. Batch disposal must
clear both caches and selection roots. It must restore both original host
proxies. Reopened canonical JSON, property lists, object count, and history
must stay unchanged.

The known empty-switch-child limitation applies
independently to both disposed records.

The attachment stays an internal, injected lower product boundary. It is
absent from `tracktemplate.api` and package initialisation. The standalone lifecycle check
also protects the explicit `TrackTemplate.FCMacro`
`activate_transition_editing()` route. The macro's normal
`FOUNDATION_RESULT = run_macro()` path stays unchanged. If a caller does not use that function, the macro imports no host,
Coin, or Qt module.

Activation must attach a
non-empty stable-ID set one time. It must reject active duplication and reuse
one transient editor. It must clear only the target document's selection. It
must retry partial attachment and observer cleanup. It must stop permanently
without reactivation.

Composition-level fault injection must prove recoverable
observer-registration rollback. Failed observer removal must keep the same
observer for a successful retry.

The check also protects the versioned
development contract. It keeps the coordinator in the host-independent UI
layer.

The same isolated runner adds a third focused real-GUI proof. It starts after the
retained one-object and representative workflows. It does not create another
orchestration loop.

On the qualified Entry/Exit document, the explicit macro
route must attach both transitions one time. Canonical JSON, built-in property
lists, history, `Shape` count, and captured public `DisplayMode` state must not
change. The route must reject a concurrent invocation and expose the existing
editor. It must preserve one edit with Undo/Redo.

Only successful explicit
activation registers the transient document observer. A save must use
FreeCAD's `slotStartSaveDocument`. Before serialisation, it must stop the
lifecycle and remove the observer. It must clear the target selection. It must keep the selection in a sibling
document. It must clear caches, proxies, and active
Coin children.

It must keep no transient marker after save and reopen. After close/reopen, another
explicit activation must reconstruct new scene nodes. It must reconstruct the
original owner-visible Exit state.

Explicit deactivation must stop that
rebuilt lifecycle before direct document close. The bounded composition adds
no automatic close or permanent loading policy. The inner sentinel is
`TRACKTEMPLATE_PHASE5_TRANSITION_EDITING_LIFECYCLE_GUI=`. The outer runner
sentinel stays `TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=`.

FreeCAD exposes display-mode registration but no qualified Python removal
operation. Disposal restores the original public display-mode enumeration and
switch selection. It clears each retained mapping and cache, but leaves one
named empty switch child. The lifecycle confines that residual to one child
per object. It rejects same-document reactivation. It adds no second child.

Document close/reopen removes it. The checks must enforce this documented
bounded limitation. They must not describe disposal as complete view-state
restoration. D-P5-002 accepts it only for the demonstrated Entry/Exit product
boundary recorded in the
[frozen Phase 5 closeout](history/phase-closeouts/PHASE5_CLOSEOUT.md#phase-5-coin-renderer-and-editing-acceptance-panel).
A PASS result from the checks alone gives no renderer, phase, startup, Workbench/menu,
migration, release, or output authority.

Phase 6 adapter-neutral Entry/Exit exact-centreline contract:

```bash
.venv/bin/python tests/validate_phase6_transition_exact_contract.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase6_transition_exact_contract.py
```

The standalone proof covers the explicit caller-owned chord-error tolerance
and segment ceiling. It covers the canonical local left-turn frame, units,
and deterministic station ordering. It covers the conservative Euler-curvature
interpolation bound and independent high-precision Fresnel-series coordinates.

It also covers zero-length and fail-closed resolution cases. The proof also covers signed-result
reuse, change, change-back, and failure atomicity.

The qualified
FreeCAD smoke proves that the additive public contract operates in the accepted
host profile. It creates no document, object, property, or Undo/Redo change.
Its sentinel is
`Phase 6 transition exact qualified FreeCAD validation passed`. This route
creates no `Part` geometry, target-format output, production clearance,
operator workflow, or Phase 6 exit evidence.

Phase 6 transient Entry/Exit exact geometry:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase6_transition_exact_geometry.py
```

This qualified-host proof constructs the verified exact centreline as one open
`Part` wire. For zero length, it constructs one vertex. One `Part::Feature` in
a hidden temporary document contains the geometry. The proof examines ordered
coordinates, bounds, polyline length, topology, and planarity. It also examines
kernel validity and deterministic signed neutral measurements.

Success,
explicit application cancellation, a failure in the cancellation check, and
injected Part-build failure
must all close the temporary document. Each case must restore the prior active
document. The editable document, its properties, and Undo/Redo history must
stay unchanged.

Its sentinel is
`Phase 6 transition transient exact geometry validation passed`. No
`Part.Shape` crosses the adapter. The adapter writes no file. The result supplies no
GUI, target-format, production-clearance, or Phase 6 exit acceptance.

Phase 6 private-development Entry/Exit DXF transaction and import:

```bash
.venv/bin/python tests/validate_phase6_transition_dxf_export.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase6_transition_dxf_export.py
```

The standalone proof covers deterministic DXF and dependency-manifest bytes.
It covers descriptor-relative destination control, resolve-to-bind removal,
and substitution. It covers post-lock substitution, directory-rename races,
and symbolic-link races. The proof also covers anonymous creation-bound staging and observed
descriptor-close abandonment.

The original interruption must
propagate on a surviving host with truthful chained `BaseException`
diagnostics. It must stay the primary interruption when an anonymous close
fails. Cleanup must attempt all remaining anonymous closes. Bound-directory
close diagnostics must not replace the original error.

Post-link/pre-sync
durability uncertainty must stay non-recoverable. The proof covers exact
zero-member, DXF-only, manifest-only, and complete-pair states. Historical
controls stay inert. It covers interruption after each addition and
next-invocation monotonic completion.

Complete-pair reuse must include directory
synchronisation. A synchronisation failure must preserve data and fail closed.
The proof covers explicit application cancellation and injected failure after one
addition. It covers initial-member and post-addition substitution.

Unsupported
primitives must fail closed. It covers complete exact-set reuse. It refuses
non-regular finals and byte collisions. Active-lock diagnostics must fail
closed. All retained-state diagnostics must be truthful.

The proof covers the
bounded D-P6-003 strict add-only, journal-free implementation. It gives no
deletion authority. TrackTemplate removes, rewrites, or replaces no published
final.

The standalone sentinel is
`Phase 6 transition DXF export validation passed`. The qualified FreeCAD proof
imports both the non-zero `LWPOLYLINE` and zero-length `POINT`, and repeats
document isolation and explicit application cancellation. It covers injected
second-addition failure, exact partial preservation, and next-invocation
completion. It also covers surviving-host interruption cleanup.

Its necessary
sentinel is
`Phase 6 transition DXF qualified FreeCAD validation passed`. These commands
stay bounded to the accepted Entry/Exit slice. Output stays
private-development with `unknown` status. They supply no GUI,
production-output, Phase 6 exit, or release acceptance.

#### Supported exporter interruption evidence

Exporter interruption evidence is interpreted against the canonical
[supported exporter failure model](ARCHITECTURE.md#supported-exporter-failure-model)
and the operator procedure in
[Recovery after an abnormally interrupted export](RECOVERY_AND_BACKUP.md#recovery-after-an-abnormally-interrupted-export).
The existing Phase 6 exporter commands above remain the durable entry points.
This section does not create a second command catalogue.

Mandatory retained evidence covers ordinary exceptions and explicit application
cancellation. It covers the expressly retained `BaseException` product
boundaries. The accepted staging, publication, durability, cleanup, and
recovery matrix also applies. The evidence must preserve each pre-existing and
published final. It must prove conservative diagnostics when durability or
retained state is uncertain. It must exercise D-P6-003 exact-partial and
exact-complete handling on the next invocation. It must retain qualified
FreeCAD import and host-execution evidence. That evidence applies only to the
documented platform and filesystem profile. Process-termination evidence is
bounded to the operating-system process limit. At that limit, the operating
system releases process-owned descriptors and advisory locks.
Restart alone is not destination-validation evidence.

Retained mandatory tests and exploratory disposable probes have different
authority. A probe outside the supported model can inform future architecture.
Arbitrary asynchronous injection at an excluded instruction-level micro-window
does not automatically show an implementation defect. It also does not
automatically prevent Exit 3. The probe prevents Exit 3 if it demonstrates
deletion, overwrite, corruption, or unsafe mutation. The same applies if it
demonstrates a supported-workflow failure or failure of an accepted recovery
control. Unsafe retry, a false diagnostic, or another mandatory-invariant
violation also prevents Exit 3. Current tranche chronology and temporary line
numbers do not belong in this durable contract. Individual probe narration
also does not belong here.

Repository recovery and ignored-data safety controls:

```bash
.venv/bin/python tools/repository_safety_audit.py
.venv/bin/python tests/validate_recovery_controls.py
.venv/bin/python tests/validate_recovery_controls.py --live-workstation
```

The audit is read-only and performs no network operation. It reports clean and
pushed checkpoint state from local remote-tracking refs. It verifies the
ignored Templot source archive and inventories local generated-data roots. It
fails closed if a requested backup target is absent or inside the repository.
It also fails closed if the target is on the same mounted filesystem. The
default validator proves deterministic control behaviour. This includes
rejection of a clean fixture without the archive. The `--live-workstation`
profile also proves the current checkout's ignored archive and hash. It proves
the branch/upstream product boundary. Neither result claims that an independent
backup or restore exists.

If you do not know the accepted commit for `origin/main`, use `git fetch`.
Before a bounded cycle with recovery risk, make sure that the checkpoint has
tracked cleanliness. Also make sure that a branch on GitHub contains the
checkpoint commit:

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

- The pull-request state `MERGED` and tracked cleanliness without a retirement
  plan
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

The recovery validator must use a temporary repository. In that repository,
it must use `git worktree remove` without `--force`. It must make sure that the
authoritative local source stays available. Before branch removal, it must show
that `git worktree list` does not contain the worktree. It must also show that
the accepted commit contains the branch tip.

Before worktree removal, the validator must examine the local-state types in
the retirement plan. It must also examine the preservation diff for the
local-state inventory. After removal, it must show that no other branch
changed.

After worktree removal, the validator must show that no other worktree changed.
It must show that the stash inventory did not change. It must also show that
files at each planned-preservation location did not change.

The retirement audit does not classify a local-state inventory item. The
recovery validator gives no removal authority.

Assess a selected or replacement external destination only with
`--backup-target ... --require-backup-target`. Backup completion and restore
evidence remain separate recovery conditions under
[RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md). The first copy, restore, and
incremental-repeat result for the repository bounded scope is in the linked
2026-07-22 evidence. It applies to the owner-confirmed complete project-data
bounded scope. The audit command alone does not prove those executed results.

Repository QA, documentation-link and residual-risk controls:

```bash
.venv/bin/python tests/validate_quality_assurance.py
```

This standard-library check protects the canonical QA and learning-document
roles. It verifies the accepted hash manifest for frozen phase, audit, and
performance records. It reconciles the frozen audit's open QA dispositions
with `current/risks.json`. It verifies each repository-internal Markdown file
target and preserves the immutable B14/B15 fingerprints. It also enforces the
`AGENTS.md` size and routing limit. The three-level task model and governance
budget are also enforced. It enforces Level 3 true-gate panel triggers and the
compact completion report in [ENGINEERING_POLICY.md](ENGINEERING_POLICY.md).
It proves only control consistency. It does not close an open risk or accept a
phase closure.

The check also examines the
[ASD-STE100 Issue 9 reference-source instructions](external/asd-ste100/README.md).
It examines their Git-exclusion product boundary. It also examines the
different functions of policy and an external reference. Normal CI does not
use the ignored PDF. A conformance record must report its official source.
Automatic validation does not prove linguistic conformance.

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
closed when its byte size or SHA-256 identity differs from the source manifest.
The PDF extractor file owner can be root or the current user. The extractor
must be a regular file. It must not be in the repository or active Python
environment. Its group and other users must not have write access. A rebuild
must reject all other PDF extractors. It must reject a source-derived index
whose identity differs from the source manifest.

The derived cache must contain metadata only. It must have the same input
identities as the source, profile, technical-term register, and retrieval
index. It must also match the manifest, tool, and PDF extractor. The tool must
accept the cache schema version. Source mode must use verified source bytes.
It must use the PDF extractor identity that the derived cache records.

Include tests for the source, derived cache, retrieval index, technical-term
status, and each output limit.

The validator must not claim linguistic conformance, certification, or
endorsement. A reviewer can use a review receipt to record full-applicability
review. The receipt must record examination of the complete applicable
requirement set. The receipt, pre-check, derived cache, and selected lookup
results do not show that this review occurred. They also do not show
conformance. Source identity validation does not make a positive rights claim.

For each material change to canonical prose, validate the authorised lifecycle:

1. The author freezes one clean exact Git candidate.
2. The STE lookup derives the frozen review scope from the last accepted document
   identity and Git.
3. One independent Documentation Reviewer returns one complete verdict for the
   frozen review scope. It is `ACCEPT`, `APPROVED_WITH_EXACT_CORRECTIONS`, or
   `BLOCKED`.
4. For `APPROVED_WITH_EXACT_CORRECTIONS`, all exact replacement wording is in
   that review and is applied once against verified preimages.
5. One final deterministic validation runs after the review or correction.

Each new review result must use schema 2. It must record the complete
`blockers` set and confirm that the set is complete. `ACCEPT` and
`APPROVED_WITH_EXACT_CORRECTIONS` must have an empty `blockers` set. `BLOCKED`
must have a nonempty `blockers` set. Each `blockers` entry must bind its exact
path to the frozen review scope. It must bind the frozen logical-unit identity,
finding, and formal Issue 9 rule identifiers. The receipt must preserve the
complete set and its exact candidate binding. It must also preserve the binding
for the frozen review scope. Validation must reject a `BLOCKED` result with no
recorded `blockers` entry.

The Documentation Review is the only linguistic conformance review. Do not run
a second Documentation Review. The final validation does not judge prose. It
must validate the official source identity and frozen candidate. It must also
validate the Git-derived frozen review scope, review result, and receipt. It
must validate expected document-level state and final content. It must reject
unrelated post-review mutation.

Do not include an untouched legacy document in the frozen review scope.
Include the complete document for the first material edit of an unreviewed
legacy document. After the document has an accepted identity, include only
materially changed complete logical units. Do not include unchanged previously
accepted prose. Keep accepted review state at document level. Do not persist
sentence, paragraph, or logical-unit workflow state that Git can derive.

`tests/validate_agent_guidance.py` must give a `FAIL` result when a canonical
owner omits one of these controls. `tests/validate_governance_semantics.py`
must reject removal or weakening of a semantic control. Automatic validation
and a deterministic pre-check must not claim or change linguistic conformance.

`tests/validate_ste100_retrieval.py` must prove whole-document first review and
untouched legacy exclusion. It must prove the later changed-unit frozen review
scope and document-level durable state. It must prove all three verdict routes,
exact correction preimages, and final identity binding. It must prove empty
`blockers` sets for both non-blocking verdicts. For `BLOCKED`, it must prove a
nonempty complete `blockers` set. It must prove exact finding and frozen-unit
binding, formal rule identifiers, and receipt preservation. A `BLOCKED` result
must produce no accepted-state proposal. The validator must reject a missing,
incomplete, empty, or changed `blockers` set. It must reject a set outside the
frozen review scope. The final validator
must reject source, frozen review scope, receipt, state, identity, or mutation
drift. A remaining linguistic, semantic, or identity failure returns to the
owner. A failure of the frozen review scope also returns to the owner.

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

This validates the analyser against a synthetic shadowing, alias, and patch
fixture. Then it checks the exact immutable B14 and accepted B15 source
fingerprints. It also checks their current structural and candidate facts.
Schema 2 uses the analyser's bounded static top-level call model. It separately
checks callers of nominated roots and callers crossing the proposed dependency
closure. It also checks dependencies that leave that closure. It does not
execute either macro.

Fail-closed release-critical workflow coverage checks:

```bash
.venv/bin/python tests/validate_phase1_workflow_coverage.py
```

This cross-checks the 14 canonical Markdown inventory rows against their
machine-readable owners and oracle states. It also checks evidence, recipe,
validator paths, gap owners, and future closure phases. It protects the exact
B14/B15 source state. Successor-only oracles with `Blocked` status must remain
visible. Passing proves coverage control. It does not give a partial workflow
later GUI, migration, production, provenance, or release authority. It gives
no such authority to a workflow with `Blocked` status.

Fail-closed railway terminology-assurance checks:

```bash
.venv/bin/python tests/validate_phase1_terminology.py
```

This validates the four assurance states, exact B14/B15 fingerprints, and
known phrase counts. It validates frozen ordinary-named evidence paths,
open-review ownership, and the future successor-product scan. It detects known
terminology drift and missing review control. It cannot determine contextual
railway correctness without the named human review.

Accepted Phase 1 closeout aggregation:

```bash
.venv/bin/python tests/validate_phase1_closeout.py
```

This reconciles source fingerprints, workflow counts and gaps, and the selected
pilot. It reconciles runtime and ingress policy, bounded performance defects,
and unmeasured target slots. It also reconciles S1 manifest, lineage, and
oracle blocks. Terminology reviews and the 10 owner decisions in
`PHASE1_CLOSEOUT.md` are included. It rejects loss of accepted phase state or
broadened host support. It rejects invented performance evidence, waived later
controls, and S1 clearance. Passing protects the 2026-07-22 acceptance. It
does not broaden the bounded Phase 2 authority.

Owner-accepted first-S1 package/evidence plan checks:

```bash
.venv/bin/python tests/validate_phase1_s1_pilot_plan.py
```

This protects all 15 S1 decision states and the recorded 2026-07-22 owner
acceptance. It protects the exact B14/B15 source and the structurally valid
package manifest with `unknown` status. It also protects bounded lineage scopes
with `Blocked` status and the comparison-only Templot oracle. If a later chair
schema exists, the validator requires attribution to the Phase 4 evidence and owner
decision. It must not attribute that schema retroactively to Phase 1. The
validator fails closed if evidence does not support a promoted designation,
licence, dependency, or rights status. The same applies to a promoted Templot
output file. Passing means that the accepted control is internally consistent.
It does not mean that the package is project-cleared.

Project dashboard and current-record consistency:

```bash
.venv/bin/python tests/validate_project_progress.py
```

This enforces the compact project-plan sections and line budget. It reconciles
the frozen Phase 5 closeout and accepted Phase 6 opening state with
`current/PHASE_EVIDENCE.md`. It validates the detailed frozen and current risk
and decision JSON registers. It protects the retired descriptive-path redirect.
It also checks the least-privilege, SHA-pinned standalone CI workflow. It does
not assess the quality of decision evidence. It does not open a phase or
replace project-owner acceptance.

<a id="fail-closed-phase-1-performance-boundary-checks"></a>

Fail-closed Phase 1 product-boundary checks for performance:

```bash
.venv/bin/python tests/validate_phase1_performance_boundaries.py
```

This verifies the exact B14/B15 and committed performance-report fingerprints.
It verifies nine declared legacy action profiles and all nested harness
relationships. It also verifies the per-run-before-median accounting rule.
Five `bounded-not-fixed` instrumentation defects remain. Four
`not-implemented-unmeasured` target-pipeline slots also remain. The check
statically protects the current premature timing-write and late solid-reuse
source ordering. It rejects double-counted children, invented budgets,
unsupported defect closure, and fabricated target measurements. It does not
execute either macro or set a latency threshold.

<a id="fail-closed-phase-1-candidate-boundary-checks"></a>

Fail-closed Phase 1 product-boundary checks for candidates:

```bash
.venv/bin/python tests/validate_phase1_candidate_boundaries.py
```

This validates the five current candidate contracts against both complete
macro fingerprints. It checks exact literal and function AST anchors and the
live structural inventory. It derives the transition parameter order and
station-data fields from source. It also derives current chair settings and
rail, timber, position, finding, support, result, and signature schemas.
Inventory schema 2 freezes the bounded static closure-cut counts. Candidate
register schema 3 records the owner-accepted transition selection. It points
to the exact pilot contract. Mutation checks prove that source drift fails
closed. Promoted chair status, a missing schema, or a changed selection must
also fail closed. The validator does not import either macro or start
extraction. It does not approve current chair data.

Selected transition-pilot contract and expanded parity grid:

```bash
.venv/bin/python tests/validate_phase1_transition_pilot.py
```

This verifies the exact B14/B15 fingerprints and three function signatures. It
verifies `GEOMETRY_TOLERANCE`, three external caller routes, and zero outgoing
project dependencies. It also verifies generated displacement, offset, and
solver grids. Current error diagnostics, B16/launcher identity, rollback rules,
and all declared evidence paths are included. The current state requires three
mechanically identical domain functions. It requires exact B14/B15/modular
value, type, and error parity. It also requires no-cache A-B-A change-back
cases and façade identity. The B16 launcher must contain no copied calculation
body. The validator executes only selected legacy function definitions for
comparison. It does not import or launch either legacy macro.

Phase 1 runtime and legacy ingress compatibility checks:

```bash
.venv/bin/python tests/validate_phase1_compatibility.py
.venv/bin/python tools/runtime_compatibility_probe.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tools/runtime_compatibility_probe.py --pass --require-qualified
```

The validator rejects a change to the exact B14/B15 fingerprints and
persisted-schema constants. It also rejects a change to the Addon metadata
intent, Python floor, host profiles, or B14/B15 ingress sets. It examines
selected migration product boundaries without importing or launching a legacy
macro. The test changes each compatibility class. It must reject each change
that the contract does not include.

The standalone probe must report `not-freecad-runtime`. The FreeCAD probe gives
evidence only when its `TRACKTEMPLATE_RUNTIME_PROBE=` record reports
`qualified`. The result must name one exact host profile:

- `linux-x86_64-flatpak-freecad-1.1.1`
- `linux-x86_64-flatpak-freecad-1.1.3`
- `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.

An exact 1.1.1 result does not qualify 1.1.3. An exact 1.1.3 result does not
qualify 1.1.2 or another 1.1.x release. A result for one exact 1.1.3 profile
does not qualify a different exact 1.1.3 profile. The probe records no user
path.

D-GOV-006 adds only the exact FreeCAD 1.1.3 profile. All host-matrix checks gave
the specified results in that runtime. The 1.1.1 evidence keeps its recorded
host identity. D-GOV-010 adds only the exact FreeCAD 1.1.3 profile with
CPython 3.13.13 and PySide6/Qt 6.11.1. The host matrix gave the specified
results in that runtime.

D-GOV-007 and D-GOV-010 define the
[hosts for Phase 6 performance evidence](PERFORMANCE_SOP.md#phase-6-performance-host-boundary).
Together, they authorise only the three compatibility-contract profiles to
supply candidate evidence for Phase 6 performance. A subsequent decision can
admit only a performance result from one of these profiles.

The validator examines new schema-2 results. Each result and summary must
record the ID and FreeCAD version of its exact host profile. One result set
must contain one exact host profile. Use one exact host profile to compare
TrackTemplate performance. A different method can compare host profiles only
if it independently shows both effects. These are the host-profile effect and
the TrackTemplate effect.

Qualification of a subsequent host profile does not authorise its performance
evidence. The validator rejects a new result unless its ID/version pair is one
of the three exact mappings. It rejects schema 1. It also rejects a
`host_profile_id` value that is not a string. It rejects an exact-geometry
receipt that records a different FreeCAD version. It rejects a result set that
contains two host profiles.

The 1.1.1 report from 2026-08-02 is a schema-1 report. It does not have a
`host_profile_id` field. It records FreeCAD 1.1.1 and platform data. It also
records the qualified-runtime contract hash. These data identify the exact
host profile for FreeCAD 1.1.1. D-GOV-007 keeps that report as 1.1.1 evidence.
The validator does not change the report.

D-GOV-007 and D-GOV-010 admit no performance result. They define no value for a
performance budget. They do not accept Exit 4 or claim better performance.
Before a performance-change claim, D-GOV-009 must record a baseline for this
profile. The previous 1.1.1-only validator rejected the 1.1.3 test result.
D-GOV-007 does not admit this test result as Exit 4 evidence.

The Phase 2 launcher uses the same evaluator through
`tracktemplate.bootstrap`. That launcher is not document-migration evidence.
Phase 4 accepted copied-target fixture evidence only for
`plain-line-spacing-matched-transition-intent`. For each new B14/B15 entity
family, the applicable phase must add its specified cases. Configuration JSON
migration is not evidence for a previous-version `.FCStd` file.

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

The test checks the Draft 2020-12 schema vocabulary and package/output
structural rules. It checks fail-closed `project-cleared` semantics and
non-copyright-rights reviews. It also checks contribution authority, duplicate
identities, and the current S1 control record. The S1 record must validate
truthfully as `unknown`. It is not expected to pass the strict release gate.

The lineage test separately enforces the bounded first-S1/core register. Both
bounded scopes must keep `Blocked` status. Each current entry with unresolved
Templot reference data or media must remain `reference-only`. That status must remain
separate from GPL source-expression compliance. Unresolved evidence and owners
must be present. All source anchors must match the immutable B14 and accepted
B15 files. When present, the ignored local Templot archive is also verified.
The test verifies five reviewed active-member hashes. A clean checkout does
not require that archive.

The other-S&C/legacy lineage test enforces the two remaining bounded scopes in
[`lineage/phase1-other-snc-legacy-lineage.json`](lineage/phase1-other-snc-legacy-lineage.json).
The file records 24 grouped dependencies. They retain their exact current
`reference-only` or `unknown` status. Each anchor matches the immutable B14 and
accepted B15 sources. The two lineage files together cover all four IDs for
the bounded audit scope. When present, the ignored archive verifies five cited
upstream-member hashes. These include the explicitly inactive
`chairs_unit_x.pas` evidence. The test also
requires the current absence of other-S&C/legacy output dependency manifests.
Adding one requires a truthful register and validation update. It must not use
an inferred positive status.

The oracle-contract test validates the exact-556b capture specification with
`Blocked` status. It also validates the local-only output-file rule. It
validates the rejected-version guard and synthetic DXF/STL semantics. When
present, the ignored source ZIP verifies the archive and nine required members. It also
verifies visible 556b revision evidence. Four named S1 component routes must
use active `math_unit.pas`. The exact Lazarus project must select the non-`_x`
math, pad, chair, and DXF units. A clean checkout does not require an executable
or raw Templot media. The test does not claim that the frozen oracle was
captured.

The generation-map test separately enforces the bounded code-1 source audit.
It protects the distinction between active and inactive project units. It
protects exact source hashes, unit conversions, and coordinate frames. It also
protects eight reference-only value groups and nine generation stages. Five
constituent/base routes and manufacturing branches are included. The
acceptance gate keeps `Blocked` status. When available, the ignored ZIP verifies
each mapped field and routine in its owning active unit. It also verifies the complete code-1
constituent sequence and DXF/STL emission functions. It does not approve the
mapped values or copy source expressions into production. It does not replace
the missing exact-capture files or independent-evidence requirements.

Local source and candidate probes are:

```bash
.venv/bin/python tools/templot_s1_oracle.py validate-spec
.venv/bin/python tools/templot_s1_oracle.py probe-source
.venv/bin/python tools/templot_s1_oracle.py \
  inspect-executable /path/to/templot_5.exe
```

`inspect-executable` returns exit status 2 for an MZ-signature executable
candidate that lacks the required exact-556b marker. It returns the same status
for the recorded rejected 5.55a fingerprint.
Do not run an accepted candidate in an everyday profile. After an isolated
capture exists, validate its bounded format semantics with:

```bash
.venv/bin/python tools/templot_s1_oracle.py inspect-artifacts \
  --dxf benchmark-output/templot-s1-oracle/<capture>.dxf \
  --stl benchmark-output/templot-s1-oracle/<capture>.stl
```

This command reports a `semantically-valid-unaccepted-capture`. It verifies
named component blocks and inserts. It verifies direct assembly and base faces,
ASCII STL structure, hashes, counts, and bounds. It cannot prove source
revision, effective GUI settings, solid equivalence, or acceptance by itself.

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

This extracts only the exact B14/B15 calculation definitions under test. It
puts them in a standalone Python namespace. It asserts representative and
limit values, invalid-input diagnostics, and station clamping. It also asserts
interpolation, duplicate-point ordering, and exact B14/B15 result equality. It
does not import FreeCAD.

Fast Phase 1 plain-line document-oracle contract checks (the test and wrapper
retain legacy `ordinary` identifiers):

```bash
.venv/bin/python tests/validate_phase1_ordinary_track.py
```

This checks volatile-value normalisation, deterministic hashing, and null and
valid shape summaries. It checks the persisted property-schema reader and the
isolated runner contract. It does not import FreeCAD. The bounded real-FreeCAD
oracle is:

```bash
tools/freecad_bridge/run-b14-ordinary-snapshot \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base.FCStd
```

Repeat `--base` to compare independent serialisations. The runner operates only
on copies and closes them without saving. It requires the frozen deep semantic
hash for the fixed plain-line curve/two-track document.

Fast Phase 1 plain-line edit lifecycle/rollback contract checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_edit.py
```

This protects separate rounded dialog-input and exact persisted-input
contracts. It protects left/right mirror comparison and the frozen right-hand
semantic hash. It also protects source-level transaction ordering and the
complete-document history sequence. Undo/redo measurement product boundaries
and isolated runner/fault-injection structure are included. The test does not
import FreeCAD. Exercise the bounded real-GUI path with:

```bash
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command acts only on a copied document. It must prove that a `+90°` to
`-90°` replacement changes only handedness fields and reflected Y bounds. It
must validate each semantic state across the exact three-entry Undo/Redo stack.
It must prove that an explicit change-back restores the initial document
exactly. It must recover the right-hand document by undoing change-back. It
must survive save/reopen with cleared history. It must reject zero angle
without document mutation. It must abort a deliberately failed replacement
transaction after generated-output removal. It must restore the isolated
preference store. It must leave the source fixture byte-identical. The v2
controlled series and its bounded B14 atomicity defect are recorded in
[benchmarks/2026-07-19-b14-plain-line-edit-lifecycle-series.md](benchmarks/2026-07-19-b14-plain-line-edit-lifecycle-series.md).
The preceding v1 replacement/rollback evidence remains in
[benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md](benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md).

Fast Phase 1 plain-line export contract checks:

```bash
.venv/bin/python tests/validate_phase1_ordinary_export.py
```

This checks frozen filenames, manifest schema, and logical-output
normalisation. It checks the B14 source fingerprint and selected-export
staging, commit, and rollback. It checks create-time post-document-commit and
per-file ordering. It also checks both isolated runner structures without
importing FreeCAD. Exercise the explicit selected-export GUI/exporter path
with:

```bash
tools/freecad_bridge/run-b14-ordinary-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command acts only on a copied document. It must create the exact 14-file
DXF/SVG/STL/STEP/CSV variant. It must preserve that variant while allocating
`_Rev_02`. It must replace a sentinel through confirmed atomic overwrite. It
must restore each destination byte after an injected mid-commit failure. It
also parses output bounds and solid/mesh topology. It requires the frozen
logical export hash. It leaves nine document objects and no staging directory.
It keeps the source and copied FCStd byte-identical. The accepted three-run
characterisation and limitations are recorded in
[benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md](benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md).

Exercise production export inside B14's normal Generate action with:

```bash
tools/freecad_bridge/run-b14-ordinary-create-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The copied-document recipe must perform one successful replacement/export. It
must also perform one deterministic final-task failure. It requires the frozen
normalised document and success-output hashes. Parsed production metrics must
equal the selected-export oracle. It requires exactly 13 tasks plus the
manifest. One clean preflight pass can contain only the expected
output-directory information item. The document must contain nine objects.
The recipe must restore preferences and preserve save/reopen persistence. The
diagnostic failure must retain the frozen 13-file partial directory. It must
retain one manifest failure row without temporary object or file leakage. That
result documents B14. It is not the accepted transaction contract for a
migrated exporter. The controlled three-run evidence is recorded in
[benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md](benchmarks/2026-07-19-b14-ordinary-track-create-time-export-series.md).

Fast Phase 1 connected-straight and stationing workflow checks:

```bash
.venv/bin/python tests/validate_phase1_straight_station.py
```

This extracts exact B14/B15 straight construction, connection validation, and
station functions. It does not import either macro. It proves B14/B15 AST and
result parity for the controlled pair. It proves exact travel-order stationing
and joins. It also proves one independent reverse/right-side two-track datum.
Negative contract checks, source-level pre-transaction ordering, and isolated
runner structure are included. Exercise the real copied-document GUI path
with:

```bash
tools/freecad_bridge/run-b14-straight-station \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command must use B14's real pair control and normal Replace action. It must
create the deterministic `600/600 mm` entrance/exit pair. It must recover the
exact base and created states through all three Undo/Redo entries. It must edit
to `750/450 mm` while preserving exact curve geometry and stable route
identities. It must recover both edit states through Undo/Redo. Raw
Settings/Template JSON must remain exact across save/reopen. The 23 objects,
12 ordered production records, and frozen workflow hash must also remain exact.
It must restore isolated preferences and leave the source fixture
byte-identical. The controlled series is recorded in
[benchmarks/2026-07-20-b14-straight-station-workflow-series.md](benchmarks/2026-07-20-b14-straight-station-workflow-series.md).
This is alignment stationing evidence, not coverage of a physical
station/platform or straight target-file export.

Fast Phase 1 standalone-turnout workflow checks:

```bash
.venv/bin/python tests/validate_phase1_turnout.py
```

This extracts the exact B14/B15 REA C10 dimension, handing, and orientation. It
extracts valid-toe, occupied-interval, and edit-summary functions. It does not
import either macro. It proves AST/result parity for the fixed analytical
contract and invalid-input diagnostics. It proves persisted host-identity
selection and source-level pre-transaction construction. It also proves the
commit/abort structure, frozen semantic hashes, and isolated
runner/fault-injection contract. Exercise the real copied-document GUI path
with:

```bash
tools/freecad_bridge/run-b14-turnout \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The command must use B14's real turnout manager. It must resolve Main Track by
persisted identity. It must create left-hand/facing `TO-001` at chainage
`746.298 mm`. Then it must change only its hand to right. It must preserve
stable object names and the exact inherited plain-line geometry. It must
recover exact before/after semantics through the single-entry creation cycle.
It must do the same through the edit Undo/Redo cycle. It must reject an
occupied-chainage creation without mutation. It must abort an injected
first-mutation edit failure. It must preserve the frozen 17-object, 10-record
right-hand state across save/reopen. It must leave the source fixture
byte-identical. It must retain top-view, manager, and full-window evidence. The
controlled series is recorded in
[benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md](benchmarks/2026-07-20-b14-standalone-turnout-workflow-series.md).
This is one B14 legacy comparison oracle, not canonical turnout data or
coverage of trailing/straight/alternate hosts, downstream timber/chair stages
or target-file export.

Fast Phase 1 crossover preview/commit feasibility contract checks:

```bash
.venv/bin/python tests/validate_phase1_crossover_feasibility.py
```

This verifies the exact B14/B15 fingerprints and crossover AST parity. It
freezes the current preview/late-complete-gate call ordering. It validates both
analytical witnesses. It fails closed if the successor zero-mutation rule is
weakened. It does not import FreeCAD or claim that the mismatch is fixed. After
reproducing the ignored base fixture, exercise the read-only FreeCAD oracle
with:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_crossover_feasibility.py
```

The oracle resolves both hosts by persisted identity. It verifies the
nine-object semantic fixture. It calculates both mapped turnout roads and the
connector. Host A chainages are `500.000` and `746.298 mm`. It creates no
document objects. The fixture bytes must remain unchanged. It must print
`Phase 1 crossover feasibility FreeCAD oracle passed`. The exact evidence and
remaining production/GUI acceptance decision is recorded in
[benchmarks/2026-07-21-b14-crossover-feasibility-characterisation.md](benchmarks/2026-07-21-b14-crossover-feasibility-characterisation.md).

Fast Phase 1 automatic-crossover-timbering contract checks:

```bash
.venv/bin/python tests/validate_phase1_crossover_timbering.py
```

This freezes the exact B14/B15 B4 source product boundary. It first normalises
B15's recompute instrumentation. It freezes the controlled result and
signatures. It also freezes the distinction between accepted semantics and
three current defects. Exercise the copied-fixture lifecycle in real FreeCAD
with:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_crossover_timbering.py
```

The oracle creates `XO-001` only in a temporary copy. It applies and reuses B4.
It checks exact Undo/Redo and save/reopen. It distinguishes display-only
invalidation from calculation-input invalidation. It clears B4 and injects the
first tagging failure. It must print
`Phase 1 crossover timbering FreeCAD oracle passed`. It must leave the source
fixture byte-identical. The retained untagged object is a required defect
witness. Display-only rebuild and nested diagnostic drift are also required
defect witnesses. They are not future product behaviour. Exact evidence and
the remaining bounded scope are in
[benchmarks/2026-07-21-b14-crossover-timbering-characterisation.md](benchmarks/2026-07-21-b14-crossover-timbering-characterisation.md).

Fast Phase 1 chair-analysis persistence/reuse contract checks:

```bash
.venv/bin/python tests/validate_phase1_chair_analysis_persistence.py
```

This freezes the inherited B14/B15 logical-analysis source product boundary.
It freezes fixed `XO-001` semantic and display digests. It also freezes
timing-persistence ordering, the effective-status scan, and the active panel
refresh route. Exercise cold calculation, unchanged reuse, reuse Undo/Redo,
and save/reopen in real FreeCAD with:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_chair_analysis_persistence.py
```

It must print `Phase 1 chair analysis persistence FreeCAD oracle passed`. It
must leave the ignored fixture byte-identical. Truncated persisted timings are
required defect witnesses. Metadata and history mutation on a cache hit are
also required defect witnesses. Repeated status scans and redundant panel
refresh are required defect witnesses. They are not accepted successor
behaviour. Exact evidence and the remaining bounded scope are in
[benchmarks/2026-07-21-b14-chair-analysis-persistence-characterisation.md](benchmarks/2026-07-21-b14-chair-analysis-persistence-characterisation.md).

Fast Phase 1 chair-analysis invalidation/presentation contract checks:

```bash
.venv/bin/python tests/validate_phase1_chair_analysis_invalidation.py
```

This classifies each normalised setting and emitted rail or timber field for
the fixed post-B4 `XO-001`. It freezes representative logical-output mutations.
It guards the source precision and order product boundary. Exercise the actual
application cache and headless diagnostic-layer topology in real FreeCAD with:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_chair_analysis_invalidation.py
```

It must print `Phase 1 chair analysis invalidation FreeCAD oracle passed`. It
must leave the ignored fixture byte-identical. The stale cache hit and
five-decimal precision alias are required legacy defect witnesses. Record-order
and downstream-setting over-invalidation are also required witnesses. The
exact-Part presentation rebuild is another required witness. These are not
accepted product behaviour. FreeCADCmd visibility is explicitly
non-authoritative. Real-GUI visibility, selection, history, and refresh remain
open. Exact evidence and the bounded scope are in
[benchmarks/2026-07-21-b14-chair-analysis-invalidation-characterisation.md](benchmarks/2026-07-21-b14-chair-analysis-invalidation-characterisation.md).

Fresh-checkout development-bridge and deterministic B14 fixture setup:

```bash
tools/freecad_bridge/setup-freecad-cli
tools/freecad_bridge/build-b14-base
```

The fixture command refuses to overwrite existing output. A bounded bridge
lifecycle check can then run `tools/freecad_bridge/run-b14-cold --stages
geometry`.

The controlled representative performance sequence is:

```bash
tools/freecad_bridge/run-b14-cold
tools/freecad_bridge/run-b14-warm --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

The warm command accepts only a completed seven-stage cold document with its
sibling `run.json`. It performs one warm-up and exactly three measured
unchanged-result iterations. It fails if object, cache-signature, chair-count,
or solid-shape identity changes. These long-running GUI performance runs are
checkpoint and performance evidence. They are not part of the fast edit loop.

Run the bounded B14-to-B15 behavioural acceptance from a completed controlled
B14 cold document with:

```bash
tools/freecad_bridge/run-b15-acceptance \
  --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

This long-running GUI check verifies exact inherited analysis and support. It
verifies non-chair leaf geometry, the B15 layout representation, and
unchanged-result reuse. It verifies controlled removal of retained B14 solids
and fresh B15 solid construction. Solid reuse and equivalence, effective
status, and save/reopen persistence are included. It also verifies rendered
manager and view evidence. The input document must not change. Its timings are
observations only. They are not approved interactive budgets.

The FreeCADCmd B15 command succeeds only with exit status zero. It must also
print `B15 FreeCAD 1.1 headless smoke test passed`. FreeCADCmd loads
command-line scripts under their filename stem instead of `__main__`. The test
has an explicit runner for that execution mode.

The existing automated coverage does not validate each B14/B15 workflow.
Select checks by the bounded scope of the change. Report uncovered paths.

## Change matrix

| Bounded scope of change | Minimum validation |
| --- | --- |
| Documentation only | Links, paths, Markdown integrity and diff review |
| Pure analytical calculation | Syntax plus focused analytical/structural tests |
| Cache/signature logic | Cold calculation, valid reuse and invalidation cases |
| FreeCAD object or persistence | Headless FreeCAD plus save/reopen and cleanup checks |
| GUI display/editing | Headless checks plus real GUI exercise |
| Development bridge or performance recipe | Fast bridge contract checks plus a bounded isolated GUI lifecycle run |
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
5. Make a parameter edit. Verify that the intended layers become dirty and
   regenerate.
6. Test undo/redo when the change affects editable document state.
7. Run explicit production validation.
8. Export each affected format to a temporary location.
9. Inspect summary and manifest diagnostics. Confirm that no transient objects
   remain.
10. Copy the performance report when the change has a resource objective.

## Failure policy

- Do not weaken an assertion solely because a refactor fails it.
- Determine whether the failure exposes a defect, an intentionally changed
  invariant, or an obsolete test product boundary.
- Obtain agreement before changing an accepted railway or production invariant.
- Record any check that could not be run and the risk it leaves.

## Observed regression obligations

The controlled B14 runs and export source/transaction audits expose seven
behaviours. Each behaviour needs a focused test with its eventual production
fix. Do not encode the current defect as the expected result only to increase
the test count.

The first four performance items below are explicitly bounded with the
repeated status scans in
[`contracts/phase1-performance-boundaries.json`](contracts/phase1-performance-boundaries.json).
This makes unsafe current measurements ineligible for optimisation selection.
It does not mark a defect fixed or replace the regression obligations.

1. Crossover preview/commit feasibility: the fail-closed Phase 1 contract and
   read-only FreeCAD oracle freeze two B14 values. They are the `500.000 mm`
   preview-pass/complete-fail witness and valid `746.298 mm` control. The
   successor regression must use the same persisted host identities and
   request. It must use the request for preview and create/edit/extend. It must
   cover both mapped turnout roads and the connector. It must reject the lower
   witness before Part construction or document/history mutation. It must
   accept the documented witness and prove later exact-build agreement. The
   characterisation does not mark that implementation fixed.
2. Chair timing persistence: the focused fixed-`XO-001` contract proves that
   cold and reused persisted `performance_timings_ms` omit five areas. They are
   metadata, diagnostic display, recompute, commit, and total work. It also
   proves that unchanged reuse rewrites the result in a new Undo entry. Preserve
   that defect witness. The successor must persist the final complete payload
   after all claimed work. It must reconcile the payload with the enclosing
   stage. A current unchanged result must cause no document/history mutation.
3. Effective-status reuse: the same contract freezes the independent rail,
   timber, and signature scan on each chair-status query. Query chair, support,
   layout, and solid status through one shared snapshot or bounded signature
   reuse. Demonstrate the bound. Assert that unchanged results are equivalent.
   Then mutate each relevant input class and verify correct invalidation.
4. Supported-solid cache product boundary and panel refresh: assert that an
   unchanged valid solid returns before rebuilding its plan and fit inputs. It
   must retain exact object and shape identity. It must not cause redundant
   parent or panel reconstruction. It must not cause document recompute. Then
   change each solid-signature input class. Prove that physical-fit validation
   and shape generation run again.
5. Create-time export transaction and final UI: the deterministic final-task
   oracle proves a B14 failure. Its post-document-commit `run_macro()` path
   retains twelve task files and the manifest when the final STEP fails. The
   later overall dialog still reports successful output creation. Preserve that
   diagnostic evidence. Before migration, make the production path use an
   accepted contract. That contract must cover all-file staging, manifest,
   rollback, cleanup, and a truthful summary.
6. Plain-line edit command atomicity: B14 records three undo transactions.
   They cover geometry replacement, production-schedule refresh, and
   material-report refresh. This exposes observable but incomplete seven- and
   eight-object states. Preserve the lifecycle evidence. Require one accepted
   application command to create one complete undo unit. Test the exact
   document after one Undo and one Redo.
7. Automatic crossover timbering lifecycle: the fixed Phase 1 oracle preserves
   B14's characterised `XO-001` records. It preserves calculation-input
   invalidation, reuse, history, and persistence. It diagnoses three behaviours
   that must not migrate. Persist one canonical returned or reused analysis
   payload. Exclude display controls from resolution signatures. Also exclude
   them from solver, geometry, and history work. Each injected failure must
   restore the exact document and history. It must retain no untagged partial
   object. Before legacy retirement, extend invalidation through each
   engineering-input class.

## Future validation assets

Before retiring a legacy path, add representative, non-sensitive fixtures or
deterministic input recipes. They must cover:

- curve/easement and multi-track generation
- turnout creation and editing
- straight- and curved-host crossovers
- wider automatic timbering and chair analysis (the fixed `XO-001` B4 and
  post-B4 logical-analysis lifecycles now have dedicated oracles)
- an exact local capture produced under the tracked frozen-Templot-S1
  constituent/assembly recipe. The recipe and validator exist. The exact 556b
  executable, fixture, and output files retain `Blocked` status
- a versioned native S1 chair-definition package with invalid/corrupt fixtures
- one non-sensitive, project-cleared calibrated scan/CAD/measurement fixture for
  the assisted S1 assimilation pilot
- lightweight preview selection/editing
- exact validation and each production export family
- failure rollback and document reopen.
