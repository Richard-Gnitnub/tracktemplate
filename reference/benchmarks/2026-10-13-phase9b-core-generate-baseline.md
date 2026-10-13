# Time and resources for Core Generate

Status: **Level 1 diagnostic evidence, 2026-10-13.**

This report records nine successful Core Generate actions in three fresh
FreeCAD GUI processes. It gives time and resource observations for one fixed
plain-line input. It gives no performance budget or improvement claim.
The [Performance SOP](../PERFORMANCE_SOP.md#current-instrumentation-boundary)
owns the method requirements. The [Project Plan](../PROJECT_PLAN.md) owns
phase and exit status.

## Owner view

| Field | Result |
| --- | --- |
| Current state | PR #172 is integrated at `2d363cf448efb7cb85397df8254004c93030e15c`. Phase 9B stays Open at 3/6. Exit 9B-6 stays Pending. |
| What changed | Separate diagnostic tools measure the existing Generate action. Product source, geometry, accepted oracles and policy stay unchanged. |
| What now works | Three fresh processes each complete three Generate actions, four-format export, file preservation and document cleanup. |
| Limitations/findings | Deep checks between actions can affect later process state. These observations are not an uncontaminated warm-cache comparison or a performance budget. |
| Owner decision | The owner's Continue instruction authorises this bounded Level 1 result through a draft pull request. It gives no new exit acceptance. |
| Next action | Publish the validated, independently reviewed draft. Integration needs a separate owner decision. |

## Exact source and host

The unchanged product source is commit
`2d363cf448efb7cb85397df8254004c93030e15c`.
The GUI series ran before the diagnostic files were committed. The hashes
below identify their exact executed content. All 440 recorded source hashes
were equal before and after each process and across the three processes.

| Diagnostic file | SHA-256 |
| --- | --- |
| `tools/core_generate_baseline.py` | `210a1d16984b7a182919cb35c9a81a6adf0b3f740ec6e4503936781689bdc43b` |
| `tools/freecad_bridge/probes/core_generate_baseline.py` | `3d1886b4c5c3270ce10b7258a5f8c4c3824a13290135eac3f0464ce2ed8d816f` |
| `tests/validate_core_generate_baseline.py` | `d289323d6703af29aba5b4768c13a2553e5493ccbece61f567a49beaf3700d59` |

The exact host profile is
`linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10`.
It uses FreeCAD commit `4fd3bf320d9566a27e60069fc8387448aaa3a094`,
OpenCASCADE 7.8.1 and PySide6 6.11.2. The Flatpak deployment stayed at
`e63d66825c4daf9adb09283488c2bc2ace92ed8b24bcf81666933226ed082fd4`.
The machine has an AMD Ryzen 5 5500, 12 logical CPUs and 32,724,360 KiB
reported memory. The system is Linux 7.0.0-38-generic, x86_64, glibc 2.39.
D-GOV-023 supplies functional host qualification. This report gives no
Phase 6 performance authority to that host.

## Method and scope

The profile identifier is `phase9b-core-generate-diagnostic-v1`.
Each process opens a separate copy of the fixed plain-line fixture. Its
SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
The radius and transition length are each 600 mm. The angle is 90 degrees,
the main width is 32 mm, and one parallel track gives two tracks.

The normal modular composition calls the unchanged `run_macro` function.
No export or product function is replaced. Each action publishes 13 payload
files across DXF, SVG, STL and STEP. Optional CSV and mandatory dependency
JSON give 15 files in each new atomic publication directory.

The timer starts before `run_macro` and stops when it returns. This is an
operator-action boundary with automated dialogs. It includes dialog
construction, configuration, confirmation, export and 25 ms dialog polling.
It excludes process launch, imports, fixture copy and opening, deep checks,
viewport capture and final document disposal. These excluded operations are
harness-enclosing work. No missing stage receives an estimated time.

Each process performs `first-generate`, `same-process-regeneration-1`, then
`same-process-regeneration-2`. The first action follows fixture inspection.
Deep semantic and native export checks occur between actions. Those checks
can affect memory allocation and cache state before the next action.
The later actions are same-process correctness observations with the same
configuration. They do not prove warm reuse.
The operating-system cache
is uncontrolled, and the first action does not represent a cold cache.

## Observed time and resources

Each cell gives the median and the minimum–maximum range across three
processes. Time is in milliseconds. RSS uses MiB (1,048,576 bytes), although
the exact JSON metric names end in `_mb`. Every action starts and ends with
nine document objects. Individual observations stay in the raw series.

| Action | Wall time, ms | Process CPU time, ms | RSS before, MiB | RSS after, MiB |
| --- | --- | --- | --- | --- |
| `first-generate` | 18654.812 (18625.688–18668.833) | 9572.336 (9556.886–9602.678) | 745.074 (712.457–745.520) | 950.383 (936.934–951.953) |
| `same-process-regeneration-1` | 18344.390 (18287.524–18429.625) | 9194.971 (9188.974–9318.722) | 951.715 (939.324–953.320) | 1015.883 (1012.680–1016.098) |
| `same-process-regeneration-2` | 18315.941 (18298.393–18316.493) | 9189.557 (9184.138–9219.062) | 1015.926 (1012.723–1016.363) | 1077.566 (1072.926–1079.246) |

RSS increases across the three actions in each process. This report does not
identify a leak or establish acceptable memory use. Deep checks and native
allocations prevent attribution from these values alone. There is no paired
comparison, speedup claim, editing-only result or result for every product
family. Exit 9B-6 still needs its required representative evidence and
provisional budgets from an agreed method.

## Correctness and retained evidence

All nine actions pass the existing document semantics and native format
checks. They preserve previous output bytes, inode identities and modification
times. Nine distinct publication directories contain complete output sets.
Dependency checks preserve the existing ten dependencies and
`unknown`/private-development classification.
Source and fixture hashes,
routing, preferences and pending configuration remain unchanged. Each process
closes all copied documents and stops its isolated FreeCAD instance.

The common document-and-output contract SHA-256 is
`4044872f46b45af032093f5080353bafacf40fcf5c09b1eec7439a910bd7b53c`.
The successful raw series is
`benchmark-output/core-generate-baseline/20261013-series02/series.json`, with
SHA-256
`d3b275c9dc70010e46ac498e3f67112d3447222c8c460920a43d1ae87b75fd65`.
Its three sample records preserve observations, qualification, checks and
source identities. Genuine FreeCAD captures are retained outside the timer.
The first capture, `sample-1/probe/completed-product.png`, has SHA-256
`de6b6ceafad4574d1ee639340dd6f41e089940d894c33515fb96134dad160dd8`.
Raw files and generated outputs remain ignored local evidence.

The focused standalone validator checks summary arithmetic, incomplete
records, invalid values, changed sources and fixtures, repeated output paths,
and failed cleanup. Ruff and Python compilation pass for all three new files.
The original GUI proof passes after the two bounded harness repairs below.

## Failed evidence and review limits

The first probe failed Ruff with nine undefined injected names (`F821`).
Explicit access through `globals()` corrected those bindings. This is a
fixture-or-harness defect. The initial classification and its later
classification correction remain preserved.

Series 01 completed three probe actions but failed during document disposal.
A separate RPC omitted `import FreeCAD as App`. The resulting `SystemExit`
also prevented the original sample record from being written.
That missing record has not been reconstructed. Series 01 remains failed evidence;
none of its timings enters this report's results. Its raw `series.json`
SHA-256 is
`a1333e6f5e08fd527d0fbe71e2fb24c972b11bdaa2d25e7dfbf2369775ad2611`.
The failure classification preserves the process log, bridge result and probe
record with their hashes.
The second repair makes the RPC independent and
preserves failed sample records. The focused tests cover both failures.

Independent Quality Review retains its initial `BLOCKED` result and closes
that cleanup blocker after the complete rerun. Finding `QR-BASELINE-002`
remains `REQUIRED_BEFORE_EXIT`: verification between actions affects later
state. A separately agreed method is necessary before a performance exit
claim. The final source review records no remaining blocker for this
diagnostic scope. Both bounded code repair passes are used (2/2).
The initial review SHA-256 is
`e2be5a7b72cc40fb77c100c515b1c25b7a3e9c7dbd6fe6e3f47c2dcc08e2a994`.
The final review SHA-256 is
`e0c623eb5491469bfa35ef52a221b0c4edaae059f30cf131d456206be47d5e01`.

This report accepts no exit, physical fit, production, output clearance or
release. Phase 9A acceptance, the 113-entry register, D-P6-008 and all existing
Phase 9B conditions remain unchanged.
