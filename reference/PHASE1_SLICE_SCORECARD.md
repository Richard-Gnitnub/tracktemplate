# Phase 1 First-Slice Scorecard

Status: **recommendation complete; project-owner decision pending**. This
scorecard recommends a first architecture pilot. It does not select a slice,
authorise source extraction, advance Phase 1 or promise an operator-visible
performance improvement.

## Decision being made

The first extraction has two possible jobs which must not be confused:

1. prove the modular package, standalone-domain import, temporary façade,
   parity comparison and rollback method with the smallest safe change; or
2. optimise a dominant operator-visible cost.

The current evidence supports the first job. It does not yet support using the
chair hotspot as the first mechanical extraction. The candidate boundary
contract is
[contracts/phase1-candidate-boundaries.json](contracts/phase1-candidate-boundaries.json),
schema 2. Its selection gate remains open.

## Evidence scale

The scorecard uses ordinal evidence rather than invented weighted totals:

- **Strong** — direct current-behaviour evidence and a bounded extraction seam;
- **Conditional** — useful evidence exists, but a named seam or contract must
  close first;
- **Weak** — representative evidence is absent or the current boundary mixes
  materially different work; and
- **Blocker** — a safe first move cannot be defined from the present boundary.

Performance ratings refer to the suitability of the evidence for selecting an
extraction, not whether the current implementation is fast.

## Candidate comparison

| Candidate | Correctness boundary | Mechanical cut | Performance evidence | Architectural value | First-slice disposition |
| --- | --- | --- | --- | --- | --- |
| Transition-length solver | **Strong** — direct numerical, endpoint, error and B14/B15 parity oracle | **Strong** — 3 platform-free definitions, 3 external closure callers, 0 outgoing definition dependencies | **Weak for speed** — exercised by workflow baselines but not isolated and not a measured hotspot | **Strong** — proves the domain package/façade/parity path with limited risk | **Recommend as the first architecture pilot, pending owner acceptance** |
| Alignment station index | **Strong** — cumulative station, clamping, errors and workflow direction are characterised | **Conditional** — 1 definition but 15 external callers and shallow mutable inputs | **Weak** — no isolated station-index timing | **Strong** — foundational domain record, but a broader migration surface | Defer until the point/alignment record contract and caller groups are planned |
| Alignment station interpolation | **Strong** — clamping, interpolation and duplicate-station ordering are characterised | **Blocker as currently cut** — the 2-definition closure includes shared `vector_xy`, producing 60 external closure callers | **Weak** — no isolated interpolation or caller-group timing | **Strong after redesign** — natural domain/FreeCAD adapter seam | Defer until pure XY/heading output is separated from `App.Vector` construction |
| Chair-analysis core | **Conditional** — substantial B15 parity/schema evidence, but permissive inputs and signature gaps remain | **Blocker for a first move** — 39 definitions, 36 B14/39 B15 external closure callers, 11 outgoing dependencies and duplicate/alias chains | **Strong family-level hotspot, weak core attribution** — chair-position analysis is 125.798 s median, but the boundary includes extraction, cache, metadata and display work | **High later value** — directly relevant to lightweight editing and reuse | Prioritise as a later measured performance slice after instrumentation, schema, signature and provenance gates |
| Curve/easement/station aggregate | Component oracles exist, but no additional aggregate contract | **Blocker** — 6 definitions and 65 external closure callers, including the shared FreeCAD vector adapter | **Weak** — mixed across complete generation/edit workflows | Too broad to teach one boundary cleanly | Reject as the first extraction unit; migrate its bounded components separately |

“Direct callers” in the original inventory meant callers of nominated roots.
Schema 2 now also records callers crossing any definition in the proposed
two-deep closure and dependencies leaving that closure. This changes the
transition cut from an apparent one caller to three, and the interpolation cut
from 30 root callers to 60 closure callers because `vector_xy` is shared. The
new cut metric is the correct mechanical-migration warning; runtime call
frequency remains a separate measurement.

## Representative profile evidence

These are measured legacy workflow observations, not accepted budgets and not
pure-function microbenchmarks:

| Boundary | Current median evidence | Relevance to the candidates |
| --- | ---: | --- |
| Plain-line left/right replacement | 2,783.694 ms | Exercises transition/alignment work, but exact-shape replacement and document work dominate the boundary |
| Connected-straight creation / edit | 2,528.073 / 2,078.244 ms | Exercises station/route behaviour without isolating station calculations |
| Standalone-turnout creation / handed edit | 1,743.967 / 1,977.051 ms | Exercises station interpolation and host mapping without isolating either |
| Controlled crossover geometry commit | 3,102.3 ms | Establishes that initial S&C geometry is material but much smaller than the later chair chain |
| Controlled crossover chair-position analysis | 125,798.2 ms | Proves the chair family is a dominant hotspot; it does not attribute cost to the four-root analytical core alone |
| Controlled crossover chair/support/layout/integration/solid chain | More than 99.3% of internal time | Supports the deferred-geometry architecture and later chair optimisation priority |
| Unchanged supported-chair panel action | 143.581 s warm versus 151.622 s cold | Proves current cache identity correctness but ineffective cost reuse; repeated extraction/signature/refresh work remains |
| Plain-line selected export | 7,885.730 ms | Baseline for the later transactional export/deferred-exact boundary |
| Plain-line create-through-export | 6,907.971 ms | Baseline for the legacy non-atomic Generate/export path |

The source reports are in [benchmarks](benchmarks/). None measures the proposed
lightweight editor or a modular transition/station function. That absence is
recorded rather than filled with an estimated saving.

## Recommendation

Recommend `transition_length_solver` as the first **architecture pilot**, not
as the first performance optimisation.

The proposed mechanical unit is:

- `clothoid_entry_displacement`;
- `transition_start_signed_offset`; and
- `solve_transition_length`.

The current closure is platform-free and has no outgoing project-definition
dependency. Within the analyser's bounded static top-level call model, its
external cut is nevertheless three callers, all of which must be planned
rather than inferred from the root-only count:

- `main_circle_centre`;
- `build_concentric_core`; and
- `prepare_track_alignment`.

The purpose is to prove the authoritative modular package and comparison
method cheaply before touching a high-fan-out station seam or the
resource-intensive chair chain. A successful extraction is allowed to produce
no perceptible speed-up; it must produce no meaningful regression.

## Required acceptance contract for the recommended pilot

Before source movement, the project owner must accept the recommendation and
the project must name a successor launcher/version. Neither immutable B14 nor
accepted-reference B15 is to be silently repurposed as the new production
version.

The extraction then requires:

1. a small standalone domain module with no FreeCAD, Qt or third-party import;
2. exact units, frames, parameter order, error diagnostics and tolerances from
   the candidate boundary register;
3. a temporary façade covering all three external closure callers;
4. legacy-versus-modular equality across the existing representative,
   endpoint, monotonic and invalid-input cases plus a reviewed parameter grid;
5. the existing plain-line, connected-straight and applicable FreeCAD workflow
   oracles unchanged;
6. a before/after supplementary calculation profile and the representative
   workflow measurement required by the performance SOP, with no material
   regression expected; and
7. a separate later change for cleanup, validation-policy changes or
   optimisation.

## Remaining profile gaps

- Correct the chair instrumentation boundary before using its internal timing
  payload to choose a core extraction.
- Isolate record extraction, analytical chair generation/validation,
  signature calculation, metadata, display and exact-solid work in the later
  chair profile.
- Define the pure domain point result and FreeCAD adapter before profiling
  station interpolation as a migration unit.
- Measure lightweight routine editing, explicit Validate/rebuild and complete
  export separately when their prototypes exist; do not count shifted cost as
  a saving.
- Freeze numerical interaction budgets only after the target architecture has
  repeatable cold/warm evidence.

## Decision state

- Recommended candidate: `transition_length_solver`.
- Recommendation class: first architecture pilot, not performance
  optimisation.
- Selected candidate: **none**.
- Owner decision required: **yes**.
- Phase 1 status: **open**.
