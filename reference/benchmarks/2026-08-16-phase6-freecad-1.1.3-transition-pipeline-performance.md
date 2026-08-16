# Phase 6 performance evidence on FreeCAD 1.1.3

Status: **The project records Level 2 candidate evidence. No decision admits
this result for Exit 4. No decision accepts a phase exit.**

## Scope and source state

This report records the accepted B16 Entry/Exit Edit, Validate, and Export
slice on the exact host profile that D-GOV-006 qualifies for FreeCAD 1.1.3.
The exact state is protected-main merge
`f370b029bb4c1ce34987dc025a741185e233df04`. The project used branch
`agent/phase6-current-host-performance-evidence`. `git status --short`
reported no tracked change.

The measurement profile changes one selected Exit from `420.000` mm to
`360.000` mm. It then builds the exact-validation artifact and creates the
private-development DXF and manifest. Each process also does one untimed
warm-up. It then does three measured cycles that reuse the unchanged result.

The measurement profile does not include fixture construction, dialog opening,
process launch, or final document disposal in the operator journey. It
measures file audits and document audits separately from the exporter call.

This tranche changed no product source, profiler, GUI sampler, schema,
compatibility contract, or output contract.

## Environment and method

- Recorded: 2026-08-16 15:14:29–15:14:49 UTC.
- Host: Linux 7.0.0-28-generic x86_64, 12 logical CPUs, and 31.2 GiB memory.
- Outer runtime: CPython 3.12.3 from the repository virtual environment.
- Qualified GUI runtime: FreeCAD 1.1.3 and OpenCASCADE 7.8.1.
- Host profile: `linux-x86_64-flatpak-freecad-1.1.3`.
- Evidence schema: `2`.
- Measurement profile: `phase6-transition-edit-validate-export-profile-v1`.
- The profiler started three GUI processes in isolation. Each process used a
  new output directory.
- Each process did one untimed warm-up and three measured reuse cycles.
- The method did not control the operating-system file cache or workstation
  scheduling.

The reproducible command was:

```bash
.venv/bin/python tools/phase6_transition_pipeline_performance.py
```

The profiler records monotonic wall time, process CPU time, RSS change, and
process high-water RSS. The parent duration includes all three child actions.
The profiler reconciles child and parent durations for each process.

## Source fingerprints

| Input | SHA-256 |
| --- | --- |
| Compatibility contract | `52ebf138a597e025ab26b085fa28ef3800c03093ed7ea7e85d3e2a9d563f8875` |
| GUI sampler | `22ea310b82523178ae32febdcb88dc6f4b6f0258a667f9e4345bae391bd0670f` |
| Host profiler | `54767faf70f23b85a2f3b008f98b78940688bf740a1d77567c71b2ad249fd6fb` |
| Accepted Phase 5 GUI sampler | `85c29b8ab6a83e9cac92d088428e5a7c98f7ba32efc26fc4c63506a94a3d4005` |
| Qualified Entry/Exit workload | `908519580389b3431b10805bf7c1054bedcd81dee0585f662e54115ddb521482` |
| Transition edit command | `7a08cbf1f95fe0b120f392d2f173ca4b4e559e5250f674dc47eff207c61c6d2b` |
| FreeCAD state adapter | `7485f5a784cda9688e9fa8e578a86ea34325fc71045204078bf127b1b1d70dc3` |
| Exact-validation application boundary | `d5583dd580dbbf9e15d20c63b0150d41d0fd93b7c4e5be01df07ca746d1d84e8` |
| Transient exact FreeCAD adapter | `f59772090c56f5ef5adf1c5f215c75dd79c95cacc07bf24fdd7afc5b923e5e09` |
| Export application boundary | `e41862d6b79c7d84d4dbf150679b389e8aa2f97837056248b147eb80b1719f5a` |
| DXF export adapter | `3296777902a9f24aad333bc75472df3f3f79b9eb7bfd84a7c3f24cafa03842b7` |
| Public composition API | `1ecb2634db0d434f3c7aa351c4bbc54a442f6b144b66e405ac842a84402c32db` |
| Coin presentation | `a6c070de492a343961a9bc213b1cf1df65fce32f122c6a3ebf1fa44c89ad3414` |
| Coin ViewProvider | `cf3573fb799d33b122396e4435b2ec128f7ced0ffc6421b59697560b55250991` |

The ignored raw record contains the full source map.

## Correctness gates

The correctness checks found no failure in the three cold journeys or nine
measured reuse cycles. Each cold journey did the selected edit and created one
Undo unit.
Each result kept two compact editable objects, two Coin layers, and 16 active
test-scene nodes. No editable object had a `Shape` property.

Validate and Export returned the same exact-result and geometry signatures.
Each cold export created one DXF and one manifest with no staging residue.
Each reuse cycle reported byte-identical reuse. Cleanup disposed two proxies
and discarded the exact cache. The document count after cleanup was zero.

The deterministic output was a 1,426-byte DXF and a 6,829-byte manifest:

| Artifact | SHA-256 |
| --- | --- |
| DXF | `f158070dd226e4b4f058820169d742d9dea9ca0ac5f7957e88d285e7f6721d63` |
| Dependency manifest | `af22ae6e5427508935133f497ee1ab8a3dda04a0777b46f2c63f10353b92ac1f` |

The manifest project status stays `unknown`. This evidence gives no production
or output-clearance authority.

## Cold observations

Wall and CPU values are milliseconds. RSS values are MiB. Each entry is the
median of three new processes with the full range in parentheses.

| Boundary | Wall median (range) | CPU median (range) | RSS change median (range) | High-water change median (range) |
| --- | ---: | ---: | ---: | ---: |
| Parameter edit | 22.106 (21.566–74.352) | 19.653 (17.141–29.964) | 0.508 (0.504–0.715) | 0.375 (0.375–0.523) |
| Explicit Validate | 73.570 (73.116–153.903) | 74.337 (74.056–88.881) | 3.543 (3.508–3.574) | 3.582 (3.520–3.691) |
| Created DXF export | 44.992 (18.748–46.410) | 7.468 (6.349–7.551) | 0.047 (0.008–0.063) | 0.000 (0.000–0.250) |
| Full journey | 142.912 (140.426–247.792) | 101.943 (99.692–125.963) | 4.113 (4.059–4.297) | 4.145 (3.957–4.215) |
| Uncovered remainder | 0.789 (0.751–0.828) | 0.747 (0.683–0.769) | — | — |

The process with the largest edit time also had the largest Validate time.
This pattern shows wall-time variation in the three-process series. The
evidence does not show its cause. The variation does not define a numerical
gate.

## Warm observations

The nine measured cycles reused the valid exact artifact and the two existing
output files. They still built and disposed the transient exact wire.

| Boundary | Wall median (range) | CPU median (range) | RSS change median (range) | High-water change median (range) |
| --- | ---: | ---: | ---: | ---: |
| Reused Validate | 4.401 (4.301–4.650) | — | — | — |
| Reused export | 5.422 (5.056–5.906) | — | — | — |
| Full reuse cycle | 10.417 (9.857–10.799) | 10.375 (10.069–10.647) | 0.004 (0.000–0.012) | 0.000 (0.000–0.000) |

The reuse measurements include exact geometry construction and validation.
They do not hide deferred exact cost.

## Comparison and classification

The 2026-08-02 report used FreeCAD 1.1.1 and a previous exact state.
The two reports use the same measurement profile, but they do not use one exact
host profile or one source state. Therefore, this report does not use their
timing difference to claim that TrackTemplate performance became better.

| Result | Classification |
| --- | --- |
| Workflow, lifecycle, cleanup, and deterministic output contracts | Unchanged. |
| Exact FreeCAD 1.1.3 host identity and schema-2 record | D-GOV-006 qualifies the exact FreeCAD 1.1.3 host profile. D-GOV-007 authorises that profile to supply candidate evidence. |
| Timing values compared with the 1.1.1 report | Host and source-state difference with no isolated TrackTemplate effect. |
| TrackTemplate improvement beyond normal noise | Unknown — the evidence does not compare one exact host profile before and after a product change. |
| Numerical budget and representative whole-layout capacity | Unknown — no owner decision defines a numerical budget. No evidence gives representative whole-layout capacity. |
| TrackTemplate compatibility defect | None found in this evidence scope. |

The series has only three cold samples. The series gives a cost record on
FreeCAD 1.1.3 but not a statistical distribution for an acceptance gate.

## Evidence disposition

The result adds evidence for subsequent decisions about PR-15 and QA-R04. It
gives a schema-2 result for a performance investigation on one exact host
profile. Their risk dispositions do not change.

This Level 2 tranche does not admit the result for Exit 4. It defines no
performance budget. It accepts no phase exit. Phase 6 stays at 2/5 accepted
exits. Exit 4 stays Pending.

The raw record for the completed run is under
`benchmark-output/freecad-bridge/phase6-transition-pipeline-runs/20260816T151429730281Z-profile/`.
Its `performance.json` SHA-256 is
`83deda4bdb01c5c5677f568ac62625572b19c3bce313af515ba4fa6b9840298a`.
The raw JSON, child logs, and output files stay ignored because they contain
local development details.
