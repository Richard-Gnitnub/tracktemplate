# B16 Transition Pilot Performance Profile

Status: **completed regression profile, accepted as Phase 3 closeout evidence
on 2026-07-22; no optimisation or interaction-budget claim.** The contracted
calculation and routed workflow measurements show no material modular-route
regression beyond observed run-to-run variation. Explicit project-owner
acceptance was recorded after the measurement completed.

## Scope and source state

The profile measures only the accepted Phase 3 transition-length pilot:

- the complete frozen calculation parity grid under the captured B15 legacy
  implementation and the B16 modular implementation; and
- the already-qualified plain-line edit and connected-straight workflows under
  the complete legacy and modular routes.

It started from pushed commit
`dc0623fa024cf1ba86891f713e7f160f52b0b38d`. At measurement time the only
working-tree changes were the untracked profiler and its fast validator. The
raw profile records their exact state; the profiler SHA-256 was
`ceaacacedfd5cd159d0ee8928cb7ad05a891f926c0e02226c8531f67d47ded72`.

The output-affecting source fingerprints remained:

| Input | SHA-256 |
| --- | --- |
| B14 immutable oracle | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 behavioural reference | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| B16 launcher | `8852d27002b444a37cdb5df56b9f31f9a9313c70276b89d18ea86198b06037fe` |
| Modular alignment domain | `aeb7ac16c0b5bced51df11989dbb2a44c8b8abd165b904fd2b4faf87abc45ac5` |
| Frozen transition-pilot contract | `1f4c50f6edb327c5bfbd947c4953ee51cf606c9a676bec1c8ee7c224d5f5b139` |
| Fixed plain-line fixture | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` |

No B14, B15, B16, domain, façade or compatibility calculation source changed
for this tranche.

## Environment and recipe

- Recorded: 2026-07-22 17:28:36–17:35:05 UTC.
- Host: Linux 6.17.0-40-generic x86-64, AMD Ryzen 5 5500, 12 logical CPUs,
  31.2 GiB physical memory.
- Standalone runtime: CPython 3.12.3 from the repository virtual environment.
- GUI runtime: qualified Flatpak FreeCAD 1.1.1.
- Calculation profile: one process, one untimed complete-grid warm-up per
  route, then nine measurements per route with legacy/modular order alternated
  each round.
- Workflow profile: three measurements per workflow and route, with one fresh
  isolated FreeCAD GUI process, copied fixture, document, module state, undo
  stack and temporary directory per measurement. Route order alternated by
  repetition.
- The isolated preference profile persisted between processes and the
  operating-system file cache was uncontrolled, as declared by the performance
  SOP.

The reproducible command was:

```bash
.venv/bin/python tools/phase3_transition_performance.py \
  --base benchmark-output/freecad-bridge/fixtures/b14-default-base-regenerated.FCStd
```

An earlier preflight attempt was excluded: the child runner rejected a new raw
artifact root before the first workflow action. The successful run retained the
existing guarded routed-workflow artifact root; the rejected process was
cleaned up and did not change the fixture.

## Calculation profile

The complete grid contains 202 cases: 105 clothoid displacements, 72 signed
offsets, 21 solver cases and four contracted error cases. Every warm-up and
measured result had the same exact type/value/error digest:
`80a1de3e60e34dbd96f0e1669b9b801ef9eb898cfd11be331a47560869beb486`.

| Metric | Legacy median (range) | Modular median (range) | Modular − legacy |
| --- | ---: | ---: | ---: |
| Wall time | 26.627 ms (26.379–27.108) | 24.507 ms (24.174–24.860) | -2.121 ms (-7.96%) |
| Process CPU | 26.613 ms (26.374–27.104) | 24.503 ms (24.170–24.849) | -2.111 ms (-7.93%) |

The modular observations are lower, but this is not claimed as an optimisation.
The functions are mechanically identical and the legacy functions are loaded
into a synthetic comparison namespace while the modular functions use their
normal imported module. The result is used only to reject a calculation
regression, not as an operator-response budget.

## Routed GUI workflow profile

The timings below are the synchronous action boundaries inside the established
GUI drivers. Process launch, macro/B16/B15 loading, fixture opening, controller
polling and later deep semantic validation are excluded. Medians and full
three-run ranges are reported in milliseconds.

| Workflow action | Span class | Legacy wall median (range) | Modular wall median (range) | Delta | Range overlap |
| --- | --- | ---: | ---: | ---: | --- |
| Plain-line left → right replacement | operator action, fresh process | 2958.5 (2744.5–2966.4) | 2840.3 (2801.5–3005.9) | -118.2 ms (-3.99%) | Yes |
| Plain-line right → left change-back | same-process correctness | 2011.9 (1995.9–2025.5) | 2011.2 (1991.9–2046.1) | -0.7 ms (-0.04%) | Yes |
| Connected-straight pair creation | operator action, fresh process | 2874.0 (2693.9–2899.9) | 2687.8 (2646.2–2875.5) | -186.3 ms (-6.48%) | Yes |
| Connected-straight length edit | same-process correctness | 2132.8 (2099.2–2149.1) | 2091.1 (2090.6–2102.4) | -41.7 ms (-1.95%) | Yes |

| Workflow action | Legacy CPU median (range) | Modular CPU median (range) | Delta |
| --- | ---: | ---: | ---: |
| Plain-line left → right replacement | 3135.4 ms (2957.1–3170.8) | 3067.7 ms (2949.7–3181.1) | -67.7 ms (-2.16%) |
| Plain-line right → left change-back | 2078.5 ms (2054.7–2134.5) | 2080.6 ms (2076.1–2100.6) | +2.1 ms (+0.10%) |
| Connected-straight pair creation | 2939.5 ms (2781.6–2941.5) | 2749.2 ms (2702.8–2930.8) | -190.4 ms (-6.48%) |
| Connected-straight length edit | 2234.8 ms (2193.6–2259.0) | 2233.6 ms (2185.0–2242.4) | -1.1 ms (-0.05%) |

The only higher modular median is 2.1 ms of CPU time in the same-process
plain-line change-back, or 0.10%; the observed ranges overlap. Every modular
wall-time median is lower and every legacy/modular wall-time range overlaps.
This supports a no-material-regression disposition without claiming a speed
improvement.

End-minus-start RSS medians were respectively 250.6/251.3 MiB, 57.9/53.1 MiB,
200.8/171.5 MiB and 64.2/57.8 MiB for legacy/modular in the four table rows.
The 0.7 MiB higher modular median in the first action lies inside almost
identical 59–62 MiB ranges. RSS is not a sampled peak. Object deltas were
exactly equal in every paired sample: `0`, `0`, `+14`, `0` in table order.

## Correctness and raw-artifact audit

All 12 GUI runs completed. Every run preserved its source fixture, retained
the requested route bindings through workflow completion, restored isolated
preferences, passed its history/save-reopen/failure checks and left no
isolated FreeCAD process. Route-independent contracts remained constant across
all three repetitions:

| Workflow | Exact contract SHA-256 | Difference count in every pair |
| --- | --- | ---: |
| Plain-line edit lifecycle | `85976aa1a154ab5afce8d51a89f7674e655b7b5d91f61795580e67f3980fc7f0` | 0 |
| Connected-straight lifecycle | `2eec8269c52b8491ac546650cad1c0c6975bc620ab3a4a845f4778d8a1379517` | 0 |

The ignored raw profile is under
`benchmark-output/freecad-bridge/phase3-transition-workflow-runs/20260722T172836981525Z-profile/`.
Its `performance.json` SHA-256 is
`a6dd3dda62519972e7a2f36f0b822817e95984121f7db66097d44495ee6b0deb`.
That file embeds the SHA-256 of every child `run.json`; each child in turn
records its disposable FCStd hash. Absolute local paths remain only in ignored
raw evidence.

## Limitations and disposition

- Three GUI repetitions meet the SOP minimum but do not define a permanent
  numerical budget or provide a broad statistical sample.
- The second action in each workflow is an equivalent same-process comparison,
  not a cold action. Invalid-input and injected-failure timings remain
  correctness observations and are deliberately excluded.
- Synchronous action timing does not include a later viewport repaint.
- The pilot does not touch deferred Validate/Export, turnout, crossover,
  timbering or chair production, so this report makes no performance claim for
  those paths.
- No optimisation, tolerance change, validation reduction, cache, thread or
  process was introduced into product code.

Decision: **the contracted Phase 3 calculation and workflow performance check
passes as regression evidence.** All technical Phase 3 exit conditions and
explicit project-owner acceptance are recorded. The closeout retains the
temporary comparison route; its actual removal remains a separate Phase 4
entry change.
