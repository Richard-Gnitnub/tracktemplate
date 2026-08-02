# Phase 6 Transition Edit/Validate/Export Performance Profile

Status: **completed bounded Level 2 performance evidence; not a Phase 6 exit,
budget, optimisation, B14-equivalence or output-clearance decision.**

## Scope and source state

This profile populates the Phase 1 `complete-edit-validate-export` measurement
slot for the accepted B16 Entry/Exit slice. It starts with one qualified
Entry/Exit pair, the Exit selected and its parameter editor open. The timed
journey then:

1. applies the accepted `420.000` to `360.000` mm parameter edit;
2. regenerates and builds the explicit exact-validation artifact;
3. creates the private-development DXF and dependency manifest; and
4. returns with every transient exact/export object cleaned up.

The profile also performs one untimed reuse warm-up followed by three measured
unchanged Validate/Export cycles in each process. It does not time initial
fixture construction, pointer selection, dialog opening, final document
disposal or process launch as part of the operator journey. Post-action file
rehashing and document audits are measured separately from the exporter call.

The final repaired series started from protected-main merge
`a5b6a79bf3e73e1673d440077bd65000986bb4c7` on branch
`agent/phase6-transition-pipeline-performance`. At measurement time the
working tree contained only the seven intended tranche paths:

- `tests/freecad_gui_profile_phase6_transition_pipeline.py`;
- `tests/validate_phase6_transition_pipeline_performance.py`; and
- `tools/phase6_transition_pipeline_performance.py`;
- `tests/validate_governance_semantics.py`;
- `reference/benchmarks/2026-08-02-phase6-transition-pipeline-performance.md`;
- `reference/current/PHASE_EVIDENCE.md`; and
- `reference/history/frozen-records.json`.

No product source changed for this tranche.

## Environment and method

- Recorded: 2026-08-02 09:12:32–09:12:54 UTC.
- Host: Linux 7.0.0-28-generic x86_64, AMD Ryzen 5 5500 class host,
  12 logical CPUs and 31.2 GiB physical memory.
- Outer runtime: CPython 3.12.3 from the repository virtual environment.
- Qualified GUI runtime: FreeCAD 1.1.1 and OpenCASCADE 7.8.1.
- Three fresh isolated FreeCAD GUI processes; empty document session and new
  output directory per process.
- One untimed warm-up and three measured same-process unchanged reuse cycles
  per process, giving nine warm observations.
- The isolated preference profile persisted between processes and the
  operating-system file cache was uncontrolled.

The reproducible command was:

```bash
.venv/bin/python tools/phase6_transition_pipeline_performance.py
```

Each stage records monotonic wall time, process CPU, end-minus-start RSS and
the process high-water RSS before and after the stage. The high-water value is
cumulative for the process: a zero stage delta means the stage did not exceed
an earlier process peak, not that it allocated no transient memory. No
continuous external sampler or accepted memory budget is implied.

The parent duration is recorded around the three child actions in each run.
Child and uncovered durations are reconciled per run before summary
statistics are calculated; independently selected medians are not added to
manufacture a total.

## Source fingerprints

| Input | SHA-256 |
| --- | --- |
| GUI sampler | `582f4ffee0c7f5d1cdb0984299b66aa83ce19093ec380972d6518e973b595ace` |
| Host profiler | `cc98efee5c9c5f4e11b88854f2189490e0d082cf4ecdc2e155ae17937861b0ab` |
| Accepted Phase 5 GUI sampler | `85c29b8ab6a83e9cac92d088428e5a7c98f7ba32efc26fc4c63506a94a3d4005` |
| Qualified Entry/Exit workload | `908519580389b3431b10805bf7c1054bedcd81dee0585f662e54115ddb521482` |
| Transition edit command | `7a08cbf1f95fe0b120f392d2f173ca4b4e559e5250f674dc47eff207c61c6d2b` |
| Exact-validation application boundary | `d5583dd580dbbf9e15d20c63b0150d41d0fd93b7c4e5be01df07ca746d1d84e8` |
| Transient exact FreeCAD adapter | `f59772090c56f5ef5adf1c5f215c75dd79c95cacc07bf24fdd7afc5b923e5e09` |
| Export application boundary | `46c5f7ddefb68b0eeba7dae2b5b3494d21d58041e8d65a44d272ef87329c89c1` |
| DXF export adapter | `dc2fa1f493a166726b5397d6555fa6800f0323d5b90e55862ac847ac25e679cd` |
| Qualified-runtime contract | `76e2b6ddba3c3194a2e284770edb8366a6aa4ea98226d80662dacecf8f106bec` |

The ignored raw record carries the remaining source fingerprints.

## Correctness gates

All three fresh samples and all nine measured reuse cycles passed before their
timings were admitted:

- exactly two compact editable document objects, two logical Coin layers and
  16 active test-scene nodes remained present through the timed journey;
- the real parameter edit changed only the selected Exit, regenerated exactly
  one preview and created one Undo unit;
- the visual-to-domain mapping digest remained
  `67c4926c828039b1e0e54c252783e542ccb44db8ae0a0d49ca1f7d7c5733ed8c`;
- the exact result built one open 24-vertex/23-edge millimetre wire and returned
  exact-result signature
  `sha256:5263563a2f652e65f1d37fa3856a13a7874165b97a09b3bd3bcf66b813c7056d`
  and
  geometry signature
  `sha256:04bf1680348bd89d317b5bc0ea26b99eba00dd2575d16618033cace6d0b0c265`;
- Validate and Export returned the same exact-result and geometry signatures;
- every exact build used a temporary FreeCAD document and restored the one
  editable document as active;
- the editable document retained zero `Shape` properties and no transient
  production object;
- every first export created exactly one DXF and one manifest with no staging
  residue; every later export reported byte-identical reuse;
- every reuse cycle left canonical, document, mapping and output snapshots
  unchanged; and
- final cleanup disposed two proxies and preview caches, discarded the exact
  cache and left no FreeCAD document or isolated process.

The deterministic output was 1,426-byte ASCII DXF plus a 6,829-byte manifest:

| Artifact | SHA-256 |
| --- | --- |
| DXF | `f158070dd226e4b4f058820169d742d9dea9ca0ac5f7957e88d285e7f6721d63` |
| Dependency manifest | `af22ae6e5427508935133f497ee1ab8a3dda04a0777b46f2c63f10353b92ac1f` |

The manifest remains deliberately `unknown`; the profile does not confer
`project-cleared` or production status.

## Cold journey observations

Wall and CPU values are milliseconds; RSS values are MiB. Every entry is the
median of three fresh processes with the complete range in parentheses.

| Boundary | Wall median (range) | CPU median (range) | RSS delta median (range) | Process-peak delta median (range) |
| --- | ---: | ---: | ---: | ---: |
| Parameter edit | 103.827 (20.950–122.129) | 30.603 (18.784–33.839) | 0.688 (0.504–0.898) | 0.688 (0.500–0.719) |
| Explicit Validate | 73.026 (72.799–75.429) | 73.907 (73.672–76.602) | 3.449 (3.199–3.512) | 3.371 (3.230–3.402) |
| Created DXF export | 41.259 (18.053–41.461) | 7.648 (7.305–7.757) | 0.074 (0.066–0.082) | 0.000 (0.000–0.000) |
| Complete edit/Validate/Export | 219.127 (112.567–239.585) | 112.352 (101.065–119.016) | 4.180 (4.082–4.211) | 3.918 (3.871–4.121) |
| Per-run uncovered remainder | 0.768 (0.765–0.813) | 0.772 (0.726–0.818) | — | — |

The fresh runs show substantial wall-time scheduling or I/O variation in the
edit and export children. Three runs meet the SOP minimum but do not establish
a distribution suitable for a numerical gate.

## Unchanged-result reuse observations

After one untimed warm-up, all nine measured cycles reused the same current
exact artifact, rebuilt and disposed the required transient exact wire, and
verified byte-identical existing output.

| Boundary | Wall median (range) | CPU median (range) | RSS delta median (range) | Process-peak delta median (range) |
| --- | ---: | ---: | ---: | ---: |
| Reused Validate | 4.313 (4.172–4.876) | 4.870 (4.683–5.368) | 0.000 (0.000–0.000) | 0.000 (0.000–0.000) |
| Reused export | 4.096 (3.815–4.818) | 4.434 (4.173–5.272) | 0.000 (0.000–0.012) | 0.000 (0.000–0.000) |
| Reuse Validate/Export cycle | 8.972 (8.525–9.997) | 9.838 (9.435–10.940) | 0.000 (0.000–0.012) | 0.000 (0.000–0.000) |

Reuse avoids analytical artifact regeneration and file creation, but it does
not skip exact geometry construction or validation. The measurements therefore
do not hide the deferred exact cost.

## Comparison boundary and disposition

The accepted Phase 5 one-set edit profile reported 81.952 ms median
(63.777–101.726). This run reports 103.827 ms (20.950–122.129) for the same
accepted edit call, but the observed ranges overlap. It therefore does not
establish an improvement beyond normal noise.

The B14 plain-line replacement and create-through-export reports include
different documents, full legacy exact-shape replacement, different output
scope and additional dialog/recompute/report work. This profile is not a B14-equivalent
comparison, and those larger legacy totals are not used to claim a speed-up.

The evidence does populate explicit Validate, export-from-validated and
complete edit-through-export timing/resource slots for this selected slice.
It materially improves Phase 6 decision readiness, but the formal performance
exit remains unresolved because an equivalent beyond-noise editing comparison
has not been accepted. No numerical budget is proposed or accepted.

## Retained regression validation

Before this evidence record was locked, retained validation passed at every
affected boundary:

- changed-source compilation and the focused standalone profiler contract;
- the `transition-gui` regression profile, including all 58 standalone
  validators, qualified persistence, Coin scene, edit lifecycle and isolated
  real-GUI ViewProvider checks; and
- separate qualified FreeCAD exact-contract, transient exact-geometry and DXF
  export checks, each with its required success sentinel.

No screenshot was taken: this tranche changes profiling, validation and
evidence only, while the automated real-GUI proof re-exercised the unchanged
presentation, selection and editing boundary.

## Failed-proof adjudication and limitations

- The first disposable host attempt used `/tmp`, which the Flatpak runtime did
  not expose at the same path. It failed before product execution and is
  classified `environment-or-profile-defect`. Its original raw log was not
  retained; the same boundary was reproduced after independent review with
  exact command, source hashes and output in the local ignored failed-proof
  audit.
- The first qualified sample completed the product journey, then the outer
  oracle rejected a mistaken frame literal. This was a
  `test-or-oracle-defect`; the accepted `canonical-local-left-turn-v1` value
  replaced it. Its original raw log was not retained; the final raw receipt,
  production contract and retained wrong-frame negative case independently
  establish the repair boundary.
- That sample also exposed garbage collection inside nested child wrappers,
  contaminating the parent with harness time. The `fixture-or-harness-defect`
  was repaired by collecting once before each parent and moving output hashing
  and document audits outside the action spans.
- The earlier successful three-process series is excluded because it used that
  contaminated boundary. The final series above reran the original proof after
  repair. The excluded raw `performance.json` is retained with SHA-256
  `0fc2ca1c73e864947b85275b7fe7cc3b40c2aec7ebf8e4948ce79e56d9672416`.
- The first retained
  `.venv/bin/python tests/validate_phase6_transition_pipeline_performance.py`
  run rejected comparison wording split by Markdown formatting. This
  `test-or-oracle-defect` was repaired by making the non-equivalence
  statement literal; the exact command then passed.
- The first final standalone pipeline run parsed all source and passed 57 of
  58 contracts, but an adversarial governance mutation was inserted relative
  to a later phase-exit anchor and therefore fell outside its intended panel
  after this section was added. This `fixture-or-harness-defect` was repaired
  by anchoring the synthetic quote beside the authority paragraph; the exact
  standalone pipeline then passed 58 of 58.
- The first independent staff review showed that the retained profiler did not
  bind the exact-geometry contract ID or compare Validate and Export
  exact-result signatures. This `fixture-or-harness-defect` was repaired at
  the test-owned oracle, with direct wrong-contract, wrong-frame and
  cross-stage-signature negative cases. The full three-process proof was then
  rerun from fresh isolated GUI processes.
- Initial fixture construction, selection/dialog opening, output consumption,
  save/reopen and failure injection are outside this timing profile. Their
  existing correctness proofs remain separate.
- High-water RSS is cumulative and end-minus-start RSS is not a continuous
  allocation trace. OS cache and workstation scheduling are uncontrolled.
- The two-object Entry/Exit pair is the accepted slice, not a whole-layout or
  representative product-capacity claim.

The successful raw record is under
`benchmark-output/freecad-bridge/phase6-transition-pipeline-runs/20260802T091232919173Z-profile/`.
Its `performance.json` SHA-256 is
`e9e501f265f94330bf0db152d9be0f8eaf5d8283004b02451dd0441f21246009`.
Raw JSON, child logs and output artifacts remain ignored because they contain
local paths. The local ignored
`20260802-failed-proof-audit.md` preserves the available failed command/source
identifiers and exact reproduced output while explicitly identifying the two
original raw-log omissions; this sanitised report retains their limits.
