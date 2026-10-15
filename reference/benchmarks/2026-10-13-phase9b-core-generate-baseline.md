# Time and resources for Core Generate

Status: **Level 1 diagnostic evidence, 2026-10-13.**

This report records nine completed Core Generate operations in three new
FreeCAD GUI processes. It records time and resources for one unchanged input
for plain line. It sets no performance limits and does not claim better
performance. The [Performance SOP](../PERFORMANCE_SOP.md#current-instrumentation-boundary)
owns the method requirements. The [Project Plan](../PROJECT_PLAN.md) owns
phase and exit status.

## Owner view

| Field | Result |
| --- | --- |
| Current state | Merge commit `2d363cf448efb7cb85397df8254004c93030e15c` contains PR #172. Phase 9B stays Open at 3/6. Exit 9B-6 stays Pending. |
| What changed | New diagnostic tools measure the Generate operation. Product source, geometry, accepted oracles and policy do not change. |
| What now works | Three new processes each complete three Generate operations, export in four formats, preserve files and close the documents. |
| Limitations/findings | Checks between operations can change the process state before the next operation. These results do not prove warm reuse or set performance limits. |
| Owner decision | The owner's Continue instruction authorises this bounded Level 1 result through a draft pull request. It gives no new exit acceptance. |
| Next action | Publish the validated, independently reviewed draft. A different owner decision is necessary for integration. |

## Exact source and host

The product source stays equal to commit
`2d363cf448efb7cb85397df8254004c93030e15c`.
The author ran the GUI tests before the author committed the diagnostic files.
The hashes below identify the exact content that the tests used. All 440
recorded source hashes were equal before and after each process and across
the three processes.

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
of memory in the system report. The system is Linux 7.0.0-38-generic, x86_64, glibc 2.39.

D-GOV-023 supplies functional host qualification. This report gives no
Phase 6 performance authority to that host.

## Method and scope

The profile identifier is `phase9b-core-generate-diagnostic-v1`.
Each process opens a different copy of the unchanged fixture for plain line.
Its SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
The radius and transition length are each 600 mm. The angle is 90 degrees,
the main width is 32 mm, and one parallel track gives two tracks.

The usual modular composition uses the unchanged `run_macro` function.
The tools replace no export or product function. Each operation writes 13
payload files across DXF, SVG, STL and STEP. Optional CSV and mandatory
dependency JSON give 15 files in each new atomic publication directory.

The timer starts before `run_macro` and stops when it returns. It measures
one operator operation with automated dialogs. It includes dialog
construction, configuration, confirmation, export and a dialog check each
25 ms.

The timer does not include process launch, imports, fixture copy and opening,
document and export checks, viewport capture or document disposal at the end.
The tools do this work outside the measured operation. The tools make no
estimate for a stage that they do not measure.

Each process does `first-generate`, `same-process-regeneration-1`, then
`same-process-regeneration-2`. The first operation follows fixture inspection.
Checks of document data and exported geometry occur between operations.
Those checks can change memory use and cache state before the next operation.
The subsequent operations use the same configuration and include the same
checks. They do not prove warm reuse.

The tool does not control the operating-system cache. The first operation
gives no evidence of a cold cache.

## Measured time and resources

Each cell gives the median and the minimum–maximum range across three
processes. Time is in milliseconds. RSS uses MiB (1,048,576 bytes), although
the exact JSON metric names end in `_mb`. Each operation starts and ends with
nine document objects. The raw records contain all measured values.

| Operation | Wall time, ms | Process CPU time, ms | RSS before, MiB | RSS after, MiB |
| --- | --- | --- | --- | --- |
| `first-generate` | 18654.812 (18625.688–18668.833) | 9572.336 (9556.886–9602.678) | 745.074 (712.457–745.520) | 950.383 (936.934–951.953) |
| `same-process-regeneration-1` | 18344.390 (18287.524–18429.625) | 9194.971 (9188.974–9318.722) | 951.715 (939.324–953.320) | 1015.883 (1012.680–1016.098) |
| `same-process-regeneration-2` | 18315.941 (18298.393–18316.493) | 9189.557 (9184.138–9219.062) | 1015.926 (1012.723–1016.363) | 1077.566 (1072.926–1079.246) |

RSS increases across the three operations in each process. This report does
not identify a leak or give acceptance for memory use. The checks and
FreeCAD memory use prevent identification of a cause from these values alone.

There is no paired comparison, evidence of better performance, result for
editing alone or result for each product family. Representative evidence and
provisional budgets from an agreed method are still necessary for Exit 9B-6.

## Validation and retained evidence

All nine operations give a PASS result from the unchanged checks of document
data and exported geometry. They preserve previous output bytes, inode
identities and modification times. Nine different publication directories
contain full output sets. Dependency checks preserve the ten dependencies
and `unknown`/private-development classification.

Source and fixture hashes stay equal. The tools restore preferences and
pending configuration and preserve routing. Each process closes all copied
documents and stops its isolated FreeCAD instance.

The document-and-output contract has the same SHA-256 for all nine operations:
`4044872f46b45af032093f5080353bafacf40fcf5c09b1eec7439a910bd7b53c`.
The completed raw record is
`benchmark-output/core-generate-baseline/20261013-series02/series.json`, with
SHA-256
`d3b275c9dc70010e46ac498e3f67112d3447222c8c460920a43d1ae87b75fd65`.
Its three sample records preserve measured values, qualification, checks and
source identities.

The tools keep captures from FreeCAD outside the measured operation.
The first capture, `sample-1/probe/completed-product.png`, has SHA-256
`de6b6ceafad4574d1ee639340dd6f41e089940d894c33515fb96134dad160dd8`.
Raw files and output files stay as ignored local evidence.

The standalone validator examines summary arithmetic, records with missing
data, invalid values, changed sources and fixtures, repeated output paths,
and errors during document disposal. Ruff and Python compilation give PASS
results for all three new files. The first GUI proof gives a PASS result
after the two bounded repairs to the tools below.

## Preserved errors and review limitations

Ruff found nine undefined names in the first runtime probe (`F821`).
Access through `globals()` corrected those bindings. The failure
classification is `fixture-or-harness-defect`. The author preserved the
initial classification and its subsequent correction.

Series 01 completed three runtime-probe operations but gave an error during
document disposal. The code for a different RPC did not include
`import FreeCAD as App`. The resulting `SystemExit` also prevented the tool
from writing the initial sample record.

The author did not reconstruct that missing record. Series 01 stays as
failed evidence. This report does not include its measured times in the
results. Its raw `series.json` SHA-256 is
`a1333e6f5e08fd527d0fbe71e2fb24c972b11bdaa2d25e7dfbf2369775ad2611`.
The failure classification preserves the process log, bridge result and
runtime-probe record with their hashes.

The second repair lets the RPC operate independently and preserves sample
records when an error occurs. The tests examine RPC document closure and
record preservation after an error.

Independent Quality Review keeps its initial `BLOCKED` result and closes
that finding after the tools complete the first proof again. Finding
`QR-BASELINE-002` stays `REQUIRED_BEFORE_EXIT`: checks between operations can
change the state before the next operation. A different agreed method is
necessary before the project can claim a performance exit. The last source
review records no remaining blocking finding for this diagnostic scope.

The author used the two bounded code repair attempts (2/2).
The initial review SHA-256 is
`e2be5a7b72cc40fb77c100c515b1c25b7a3e9c7dbd6fe6e3f47c2dcc08e2a994`.
The last review SHA-256 is
`e0c623eb5491469bfa35ef52a221b0c4edaae059f30cf131d456206be47d5e01`.

This report gives no acceptance for an exit, physical fit, production,
output clearance or release. Phase 9A acceptance, the 113-entry register,
D-P6-008 and all Phase 9B conditions stay unchanged.
