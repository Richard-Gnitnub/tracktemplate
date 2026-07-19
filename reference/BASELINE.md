# Phase 0 Baseline Record

Status: automated checkpoint evidence, controlled three-run B14 cold-process and three-iteration unchanged-result warm-reuse series, and reproducible bridge/fixture bootstrap were captured on 2026-07-19. Phase 0 remains open for B14/B15 acceptance and licence/provenance decisions.

## Purpose

This record identifies the exact pre-modular source, environment, validations, exclusions, and known gaps. It is evidence for Phase 0 of [PROJECT_PLAN.md](PROJECT_PLAN.md), not a claim that every operator workflow is already covered.

## Repository starting point

| Item | Recorded value |
| --- | --- |
| Repository | `https://github.com/Richard-Gnitnub/tracktemplate.git` |
| Branch | `main`, tracking `origin/main` |
| Starting commit | `3bf82cc33abb070e2333829f1c297365c9441d4e` |
| Starting commit subject | `Initial commit: add AdvancedTurnout macro` |
| Initially tracked product source | `AdvancedTurnout.FCMacro` only |
| Phase 0 capture date | 2026-07-19, Europe/London |

The B14 file has no working-tree diff from the starting commit. Phase 0 documentation and test work has not changed either macro.

The reviewed source checkpoint was committed as `989869c` (`Establish Phase 0 baseline checkpoint`) and pushed to `origin/main` on 2026-07-19.

## Version roles and source fingerprints

| Role | File | Version assignments | Lines | Bytes | SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| Behavioural baseline | `AdvancedTurnout.FCMacro` | two assignments of `10.2A8A7B14` | 47,436 | 2,242,840 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| Candidate | `model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro` | three assignments of `10.2A8A7B15` | 48,286 | 2,286,863 | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |

B14 remains the behavioural reference and B15 remains a candidate until representative GUI comparison and user acceptance say otherwise. File hashes must be recalculated if either source changes; a changed hash is a different baseline.

## Validation assets

| File | Purpose | Lines | Bytes | SHA-256 at capture |
| --- | --- | ---: | ---: | --- |
| `tests/validate_b15.py` | Fast B15 structural/analytical checks and selected B14 comparison | 357 | 13,822 | `c439ddad3f43bbf99bc2564f551b6e044ad49964573fbb0163ccbd10d0e180c1` |
| `tests/freecad_validate_b15.py` | Real FreeCAD chair-display smoke test | 87 | 3,413 | `c513dae82e3ec7203fc2f9cdbcab7c6073f5b114938487b9dcae9b91315ab5da` |

During Phase 0, the documented FreeCAD command was found to exit successfully without executing `validate()`: FreeCADCmd gives a command-line script its filename stem as `__name__`, not `__main__`. The test now supports that execution mode, converts assertion failures into a non-zero exit, and prints an explicit success sentinel. This was a test-runner correction only; macro source was not changed.

## Captured environment

| Component | Recorded value |
| --- | --- |
| Operating system | Linux Mint 22.3, x86_64 |
| Kernel | Linux 6.17.0-40-generic |
| CPU | AMD Ryzen 5 5500, 6 cores / 12 threads |
| Installed memory | 31 GiB usable reported by the operating system; 2 GiB swap |
| Repository Python | CPython 3.12.3 from `.venv`, GCC 13.3.0 |
| Git | 2.43.0 at `/usr/bin/git` |
| FreeCAD | 1.1.1, revision 44874, build hash `0108fd4b4850cc46e625b60e53cea7a7bbe69f8d` |
| FreeCAD Python path | Python 3.13 standard-library and site-package paths reported by the Flatpak build |
| FreeCAD installation | System Flatpak `org.freecad.FreeCAD`, stable x86_64 |
| FreeCAD Flatpak commit | `2d9baee388a50345bd8eaf47f9e74885267951c0cf0dab7e261d499fa428153f` |
| Flatpak runtime | `org.kde.Platform/x86_64/6.10` |

Available memory and process state vary between runs. Performance reports must still capture the fresh process/document/cache state required by [PERFORMANCE_SOP.md](PERFORMANCE_SOP.md).

## Automated validation results

Captured on 2026-07-19 from the repository root.

### Macro syntax

```bash
.venv/bin/python -c "import ast, pathlib; files=['AdvancedTurnout.FCMacro','model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8'), filename=f) for f in files]; print('Macro syntax checks passed')"
```

Result: **PASS** — `Macro syntax checks passed`.

### B15 structural and analytical validation

```bash
.venv/bin/python tests/validate_b15.py
```

Result: **PASS** — `B15 headless validation passed`.

### Real FreeCAD 1.1 headless smoke test

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD tests/freecad_validate_b15.py
```

Result: **PASS** — exit status zero and `B15 FreeCAD 1.1 headless smoke test passed` printed after the runner correction described above.

These command durations are not performance benchmarks. They establish current source/test execution only.

## Repository exclusions

The Phase 0 `.gitignore` deliberately excludes:

- `.idea/`, `.vscode/`, `.venv/`, local tool caches, and Python bytecode;
- the PyCharm starter `main.py`, which is not a product entry point;
- credentials/environment files;
- repository-local benchmark and production-output directories;
- FreeCAD backup/recovery files, while leaving intentional `.FCStd` fixtures trackable;
- `reference/t5_files_556b_06_feb_2025.zip` pending the decision below.

No ignored file is deleted. If an ignored path later becomes intentional source or a fixture, change the narrow rule explicitly rather than forcing an unexplained add.

## Local reference evidence and licensing decision

`reference/t5_files_556b_06_feb_2025.zip` is kept locally as read-only source evidence and is not in the Phase 0 checkpoint set.

| Item | Recorded value |
| --- | --- |
| File size | 2,350,856 bytes |
| SHA-256 | `2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3` |
| Archive contents | 156 entries; 13,862,960 uncompressed bytes |
| Identification | `Templot5`, described in the included README as the open-source version of Templot by Martin Wynne |
| Included licence texts | GNU General Public License version 3 |

Open decisions before committing the archive or copying/adapting its source:

1. Confirm where this exact snapshot came from and whether the archive should be redistributed in this repository.
2. Determine the TrackTemplateMacro project licence and required attribution/notices.
3. Record whether current macro code is independently implemented, derived from, translated from, or incorporates any Templot5 source.

This record identifies the issue; it is not legal advice or a conclusion about derivative-work status.

## Representative GUI and performance baseline

Status: **COMPLETE FOR THE DEFINED B14 `XO-001` PERFORMANCE SCOPE — like-for-like three-run cold-process and three-iteration unchanged-result warm-reuse series are preserved, along with one earlier accumulated-document observation. The local bridge and fixture are reconstructable from tracked inputs. This is not whole-product pipeline coverage.**

The supplied Crossover `XO-001` report and derived arithmetic are recorded in [benchmarks/2026-07-19-b14-crossover-xo-001.md](benchmarks/2026-07-19-b14-crossover-xo-001.md). It reports 1,980.77 seconds across nine entries from a long-lived document without a fresh process or timing reset. It includes repeated 3D preparation and bounded-support actions, with no intervening parameter changes reported. Treat it as evidence of accumulated-document behaviour, not a controlled cold/warm benchmark or a benchmark of the complete curve-to-export product pipeline.

The first controlled run is recorded in [benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-01.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-01.md). A fresh isolated FreeCAD 1.1.1 process opened a nine-object copy of the fixed B14 default two-track curve, placed `XO-001` between Main Track and Track 2 at Host A chainage 746.298 mm, and completed geometry, timbering, chair analysis, bounded support, 2D fit, integration and 3D chair preparation. All post-stage domain assertions passed. B14 recorded 695.262 seconds and +445.7 MB RSS; the external controller recorded 714.987 seconds from pre-open snapshot through reporting, save and final inventory, with process RSS increasing from 488.234 MB to 1083.188 MB.

The like-for-like current-controller cold series is recorded in
[benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-cold-series.md).
Its three internal B14 totals were 686.691, 680.027 and 679.098 seconds, with a
median of 680.027 seconds and range of 7.593 seconds. Complete controller
intervals were 707.246, 700.818 and 698.573 seconds, with a median of 700.818
seconds and range of 8.673 seconds. Every run ended with 27 objects and passed
semantic-fixture, stage-state, dialog, rendered-evidence and exact-instance
shutdown checks. The earlier run 01 remains preliminary internal evidence but
is excluded from those series statistics because its outer evidence-capture
boundary predates the current controller.

The unchanged-result series is recorded in
[benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md](benchmarks/2026-07-19-b14-crossover-xo-001-automated-warm-reuse-series.md).
A fresh isolated process opened the completed cold-run document, validated its
27-object and 119-solid state, performed one excluded warm-up, then measured
the real **Generate supported chair solids** panel action three times. Every
iteration reported `unchanged_result_reused=True` and retained identical object,
signature and shape fingerprints. The action median was 143.581 seconds with a
0.415-second range, versus the same cold Stage 7 median of 151.622 seconds: only
8.041 seconds (5.30%) were saved. The direct reuse function median was 29.670
seconds; post-function panel refresh accounted for about 113.954 seconds and a
separate six-status audit took 22.905 seconds. This establishes correct but
ineffective cost reuse without misclassifying destructive stages as warm work.

The local commands are:

```bash
tools/freecad_bridge/run-b14-cold
tools/freecad_bridge/run-b14-warm --base benchmark-output/freecad-bridge/runs/<cold-run-id>/b14-crossover.FCStd
```

The bridge and exact recipe are documented in [`tools/freecad_bridge/README.md`](../tools/freecad_bridge/README.md). The third-party checkout and FCStd remain ignored local artifacts, but tracked tooling now recreates them: `setup-freecad-cli` pins and verifies the reviewed six-file patch with 22 focused tests, and `build-b14-base` constructs the default two-centreline document in an empty isolated FreeCAD session without operator clicks. The builder records binary and semantic manifests and refuses overwrites.

An independent regeneration produced a 636,344-byte FCStd with binary SHA-256
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
Its bytes differ from the original 641,206-byte fixture, as FreeCAD
serialisation permits, but both fixtures produced semantic SHA-256
`a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e`
over the exact object roles/types, curve inputs, centreline identities and
centreline lengths. A subsequent geometry-only cold lifecycle check completed
against the original fixture using stable centreline identity plus chainage and
confirmed the isolated Flatpak instance had stopped. This check validates the
recipe/lifecycle; it is not an additional full-workflow performance run.

For any additional representative recipe, record:

- exact B14 or B15 filename/version;
- new document, saved document, or deterministic construction recipe;
- curve/easement, station, track, turnout, crossover, timber, chair, and export settings used;
- exact guided-stage sequence;
- selected preview/shape/export options;
- cold or warm cache state;
- FreeCAD process restart and starting object count.

The initial like-for-like cold and unchanged-result warm series are complete. Preserve each complete report and report median and range without mixing cold and warm results. Rerunning destructive construction stages is not automatically a cache-reuse test. Use B14's report plus the bridge's external timings and state evidence; never estimate missing stages from source or validation-command durations.

## Known validation gaps

- Current automated tests concentrate on B15 chair representation, selected chair/timber calculations, cache reuse, recompute measurement, and selected B14/B15 function equality.
- They do not cover every curve/easement, station, multiple-track, turnout, crossover, timbering, persistence, GUI editing, undo/redo, or production-export workflow.
- The FreeCAD smoke test checks a bounded chair batch and object-count behaviour; it is not a whole-document integration test.
- The deterministic B14 fixture, stable centreline/chainage recipe and reviewed bridge patch are reconstructable from tracked inputs; a fresh machine still requires the documented FreeCAD Flatpak and ordinary local tool prerequisites.
- Controlled three-run cold-process and unchanged-result warm-reuse crossover series exist, but whole-product pipeline instrumentation does not yet cover curve/easement, station, multiple-track, editing, Validate, and Export paths.
- No save/reopen, legacy-document migration, or complete SVG/DXF/STL/STEP equivalence matrix has yet been run.

These gaps become inputs to Phase 1 characterisation. They do not justify weakening the Phase 0 checkpoint gate.

## Phase 0 gate status

| Gate item | Status |
| --- | --- |
| Conservative repository exclusions | Complete |
| Exact source versions, fingerprints, and environment | Complete |
| Syntax and B15 analytical/structural validation | Pass |
| Genuine FreeCAD headless assertions | Pass |
| Intended checkpoint contents reviewed | Complete |
| Source checkpoint committed and pushed | Complete — source checkpoint `989869c` on `origin/main` |
| Benchmark/tooling checkpoint | Committed locally; push pending |
| Representative GUI recipe and cold/warm reports | Complete for the defined B14 `XO-001` scope — exact recipe, reproducible prerequisites, like-for-like three-run cold series and three-iteration unchanged-result warm series captured; whole-product extension belongs to Phase 1 |
| B14/B15 behavioural acceptance | B14 baseline / B15 candidate; final acceptance pending |
| Reference ZIP redistribution and project licence/provenance | Pending decision; ZIP remains local |

Phase 0 remains open.
