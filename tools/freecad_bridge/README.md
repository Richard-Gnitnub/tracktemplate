# FreeCAD development bridge

This tooling gives the development agent a controlled FreeCAD GUI session for
document inspection, UI observation and long-running benchmarks. It is not a
TrackTemplateMacro runtime dependency.

## Isolation and safety

- The third-party `freecad-cli` checkout lives under ignored `.devtools/`.
- FreeCAD uses ignored configuration and results under
  `benchmark-output/freecad-bridge/`.
- Its FreeCAD user home/data paths and XDG data, configuration and cache
  directories are isolated there as well, so installed addons and cache locks
  from everyday FreeCAD are not shared. Each automated isolated run receives a
  fresh temporary/recovery directory which is removed after its exact FreeCAD
  instance stops, preventing a failed run's recovery record from contaminating
  the next run.
- The addon is supplied only through this session's `--module-path`; it is not
  installed into the normal FreeCAD `Mod` directory.
- The server binds to `127.0.0.1`, uses the dedicated port `19875`, and requires
  a generated local token.
- Long operations use asynchronous jobs and can be polled for up to six hours.
- The launcher records its exact Flatpak instance ID and requests parent-death
  cleanup; the isolated lifecycle wrapper uses that ID as a shutdown fallback.

Do not open an irreplaceable document in this session. Use a copy or a
deterministic construction recipe for benchmark work.

## Local development checkout

The current spike is based on upstream commit
`660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7` on a local
`tracktemplate-dev-bridge` branch. Its patch adds PySide6 compatibility,
authenticated local calls, configurable Flatpak-session settings and
asynchronous jobs. The checkout is intentionally not vendored into the product
repository.

The checkout remains ignored, but its reviewed patch is tracked. Prepare or
verify the pinned checkout from a fresh repository clone with:

```bash
tools/freecad_bridge/setup-freecad-cli
```

The command checks out the exact upstream commit, applies only
`freecad-cli-tracktemplate.patch`, refuses an unexpected checkout state, and
runs the 22 focused bridge tests without adding pytest to the product project.

## Commands

Start the dedicated GUI session:

```bash
tools/freecad_bridge/launch-freecad
```

From another terminal, verify the connection and inspect it:

```bash
tools/freecad_bridge/freecad-cli ping
tools/freecad_bridge/freecad-cli execute-code --file tools/freecad_bridge/probes/session_snapshot.py
tools/freecad_bridge/freecad-cli execute-code --file tools/freecad_bridge/probes/ui_snapshot.py
```

Load B14 without opening its main curve dialog, then show the trackwork manager:

```bash
tools/freecad_bridge/freecad-cli submit-code --file tools/freecad_bridge/probes/load_b14.py
tools/freecad_bridge/freecad-cli execute-code --file tools/freecad_bridge/probes/show_trackwork_manager.py
tools/freecad_bridge/freecad-cli execute-code --file tools/freecad_bridge/probes/trackwork_manager_snapshot.py
tools/freecad_bridge/freecad-cli execute-code --file tools/freecad_bridge/probes/capture_manager_screenshot.py
tools/freecad_bridge/freecad-cli execute-code --file tools/freecad_bridge/probes/capture_active_dialog.py
tools/freecad_bridge/freecad-cli submit-code --file tools/freecad_bridge/probes/scan_crossover_chainages.py
tools/freecad_bridge/freecad-cli execute-code --file tools/freecad_bridge/probes/capture_active_view.py
```

`submit-code` returns a job identifier. Use `job-status` or `wait-job` with that
identifier. Asynchronous jobs belong to one FreeCAD process and disappear when
that process exits.

The B14 recipe below defines its document semantics, centreline identities,
chainage, settings, stage order and cold-process qualification. Additional
recipes must make the same choices explicit before their timings are comparable.

## Reproducible B14 fixture

On a fresh checkout, prepare the pinned bridge and build the ignored base
fixture with:

```bash
tools/freecad_bridge/setup-freecad-cli
tools/freecad_bridge/build-b14-base
```

The builder starts an empty isolated FreeCAD process, forces the explicit B14
default inputs, rejects any unexpected dialog, validates the exact nine-object
semantic state, and refuses to overwrite an existing fixture or manifest. It
creates:

```text
benchmark-output/freecad-bridge/fixtures/b14-default-base.FCStd
benchmark-output/freecad-bridge/fixtures/b14-default-base.manifest.json
```

The manifest records the macro and FCStd hashes plus a semantic hash over object
roles/types, curve parameters, centreline identities and centreline lengths.
FreeCAD may serialise semantically equivalent documents to different bytes, so
the semantic hash is the fixture-equivalence contract. The original
641,206-byte fixture and the independently regenerated 636,344-byte fixture both
produced semantic SHA-256
`a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e`.

The fixture contains the untouched result of B14's default two-track curve
dialog and no managed turnout/crossover. The runner revalidates those semantics
and copies the fixture into a new timestamped run directory; it never modifies
the fixture itself.

## Phase 1 ordinary-track document oracle

Capture the deeper read-only persistence, identity, production-record and shape
contract of one fixture with:

```bash
tools/freecad_bridge/run-b14-ordinary-snapshot
```

Repeat `--base` to compare independently serialised fixtures in the same
isolated run:

```bash
tools/freecad_bridge/run-b14-ordinary-snapshot \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base.FCStd \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The runner copies every input, loads B14 without its launch dialog, opens each
copy, captures the oracle, closes it without saving, and fails unless all
supplied fixtures have the same semantic hash. Raw JSON and copied FCStd files
remain ignored under `benchmark-output/freecad-bridge/ordinary-runs/`.

This is characterisation evidence, not a performance benchmark. It preserves
production-record list order and exact stable identities, but replaces the
generated `created_at` and disabled-platform `manager_id` values with named
placeholders. It deliberately excludes FreeCAD shape hash codes. The two B14
fixtures above have different binary hashes but both produce the Phase 1 deep
semantic SHA-256
`b5641d79ff1fd77956f3ade8372da2f5b0dd50b6d42945aa611207242278b656`.

## Phase 1 ordinary-track edit and rollback oracle

Drive B14's real curve dialog through one handedness replacement, persistence,
invalid input and an injected transaction abort with:

```bash
tools/freecad_bridge/run-b14-ordinary-edit \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The wrapper launches a fresh isolated FreeCAD process and copies the supplied
fixture into an ignored timestamped directory. It changes the copied default
curve from `+90°` left-hand to `-90°` right-hand through B14's normal
**Replace all existing generated templates** path, validates the complete
mirrored document, saves, closes and reopens it, then proves both a zero-angle
validation failure and a post-removal `abortTransaction()` leave the document
unchanged. A final reopen must retain the frozen right-hand semantic SHA-256
`4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4`.

The fault injection is development instrumentation: it replaces the first
generated-object tagging call only long enough to fail inside the open
replacement transaction after old outputs have been removed. The runner also
checks and restores the isolated profile's affected last-used-input settings.
It never modifies the source fixture. Raw evidence remains ignored under
`benchmark-output/freecad-bridge/ordinary-edit-runs/`; the controlled series is
recorded in
[`reference/benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md`](../../reference/benchmarks/2026-07-19-b14-ordinary-track-edit-rollback-series.md).

## Phase 1 ordinary-track selected-export oracle

Drive B14's real selected-production export dialog through initial output,
non-overwrite revisioning, confirmed overwrite and an injected commit failure:

```bash
tools/freecad_bridge/run-b14-ordinary-export \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

The wrapper launches a fresh isolated FreeCAD process and operates only on a
copy of the fixed nine-object fixture. It selects the complete `SET-001`
template set, DXF/SVG/STL/STEP, individual plus combined files, a manifest and
exporter-bound probes. The recipe validates the exact 14-file base and
`_Rev_02` inventories, the 15-row manifest, parsed 2D bounds, STEP/STL
topology, the frozen logical export hash, source/document non-mutation and
staging cleanup. Its failure hook wraps the real atomic commit and fails after
one destination replacement so the real backup restoration is exercised.

Raw evidence remains ignored under
`benchmark-output/freecad-bridge/ordinary-export-runs/`; the controlled series
is recorded in
[`reference/benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md`](../../reference/benchmarks/2026-07-19-b14-ordinary-track-selected-export-series.md).
This oracle covers the explicit selected-export transaction. B14's separate
create-time export path, cancellation, other scopes/entity families and future
deferred exact-shape construction remain Phase 1 gaps.

## Automated B14 cold run

After the local base fixture has been prepared, one command launches a fresh
isolated FreeCAD process, copies the base document, drives every B14 crossover
stage, saves its JSON state, report, final top view, manager image, working
document and startup logs under ignored `benchmark-output/freecad-bridge/runs/`,
and terminates only that process:

```bash
tools/freecad_bridge/run-b14-cold
```

A bounded lifecycle smoke test may select a prefix of the sequence:

```bash
tools/freecad_bridge/run-b14-cold --stages geometry,timber
```

The sanitised Phase 0 three-run result is recorded in
[`reference/benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md`](../../reference/benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md).

The pinned recipe resolves Main Track and Track 2 by persisted template-set,
track-number and track-name identity, never by UI row order. It places the
crossover from Host A's centreline at chainage `746.298 mm`; no free XYZ datum is
part of the recipe. It uses the default 600 mm requested minimum radius,
automatic handing, and the normal geometry, timber, chair, support, 2D layout,
integration and optional 3D stages. The chainage was chosen by the read-only
scanner because the complete resulting minimum radius is safely above 600 mm.
Unexpected dialogs fail the run after their text is captured; only the known
geometry and integration confirmation questions are approved. Each stage must
also reach its expected B14 status or the run fails. The final capture rejects a
sampled single-colour top view, so a non-empty but unrendered PNG is not accepted
as GUI evidence.

## Automated B14 warm reuse

Use the completed FCStd from a successful full cold run as the explicit input:

```bash
tools/freecad_bridge/run-b14-warm --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

The runner verifies the document's sibling `run.json`, exact macro and semantic
base, seven-stage sequence, completed state and 27-object inventory before
copying it into a new ignored warm-run directory. A fresh isolated process
opens that copy, performs one warm-up, then exactly three same-process
measurements of the actual **Generate supported chair solids** panel action. It
requires `unchanged_result_reused=True` plus stable object, cache-signature,
chair-count and solid-shape fingerprints on every iteration. Neither the source
nor copied document is saved.

This recipe deliberately excludes timbering, model support, 2D layout and
integration because replaying constructive or invalidating stages would be a
false cache-reuse test. Its result is stage-specific and must not be compared
with the full cold-workflow total. The controlled Phase 0 result is recorded in
[`reference/benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md`](../../reference/benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md).

## Automated B14-to-B15 behavioural acceptance

Use a completed document from a successful full B14 cold run as the immutable
input:

```bash
tools/freecad_bridge/run-b15-acceptance \
  --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

The runner verifies the cold run and source hashes, copies the document into a
new ignored acceptance directory, then opens that copy in one fresh isolated
FreeCAD process. It loads B15 without its startup dialog and drives the real
crossover-manager actions for chair analysis, bounded model support, first B15
2D layout, and unchanged-layout reuse. Through the real maintenance control it
then removes the retained B14 solids, constructs fresh B15 solids, and repeats
the unchanged solid action to prove reuse. Finally it saves, closes and reopens
the document before checking effective statuses and capturing the real manager
and top view.

The acceptance oracle requires stable persisted host identities and Host A
chainage `746.298 mm`, exact inherited chair-analysis semantics, unchanged
bounded-support decisions, unchanged non-chair leaf `Part` geometry, 119
equivalent supported-chair solids, B15 representation revision 2, no document
or shape mutation on valid layout/solid reuse, fresh B15 reconstruction of the
exact 119-solid B14 topology and bounds, and an exact save/reopen round trip. It
also verifies that the completed B14 source document was not modified.

This is a correctness qualification, not a performance benchmark. Action
durations are recorded as observations, but the current cold and
unchanged-result durations are explicitly not approved human-use budgets. The
sanitised Phase 0 result is recorded in
[`reference/benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md`](../../reference/benchmarks/2026-07-19-b14-to-b15-chair-acceptance.md).
