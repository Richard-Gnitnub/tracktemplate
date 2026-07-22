# Phase 4 Canonical State, Signatures, and Persistence Evidence

Status: **Active.** The project owner explicitly instructed the project to
start Phase 4 on 2026-07-22. No Phase 4 exit condition is claimed complete.

## Bounded opening tranche

The first tranche establishes a FreeCAD-independent canonical-state boundary
for the parity-proven transition-length slice. It does not yet write a FreeCAD
property, migrate a legacy document, create preview or exact geometry, define a
chair package, or remove the retained Phase 3 comparison route.

The tranche started from pushed Phase 3 closeout commit
`bf4e64e1a82f13b86ceba0f678d5a5d84c49bf84`. B14 and B15 remain immutable:

- B14: `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`
- B15: `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`

## Canonical record boundary

`tracktemplate.domain.transition.TransitionIntent` is an immutable standard-
library record. It contains only durable parametric intent and metadata needed
by the accepted solver:

| Field | Meaning |
| --- | --- |
| `transition_id` | Caller-supplied, non-empty stable identity; replacement of an existing record cannot change it |
| `circle_centre_y_mm` | Finite millimetres in canonical local left-turn model space |
| `radius_mm` | Finite model-space millimetres; the mechanically preserved solver still owns its positive-radius diagnostic |
| `target_signed_offset_mm` | Finite signed model-space millimetres in canonical local Y |
| `total_angle_rad` | Finite radians; positive angle remains the accepted caller precondition rather than a silently added solver rule |
| `track_name`, `end_name` | Diagnostic labels, not stable identities and not numerical-result inputs |

The record normalises accepted integer or float inputs to finite Python
`float` values and rejects booleans, NaN and infinities. That validation belongs
to the new canonical-state boundary; the three mechanically extracted Phase 3
functions remain byte-for-byte AST-equivalent to B15.

## Provisional transition schema v1

`tracktemplate.application.transition_state` owns the provisional development
schema. The writer emits version 1 and the reader currently accepts exactly
version 1. This is not yet the owner-agreed complete Phase 4 schema/version
window: the chair-definition version window, legacy family migrations and
FreeCAD property envelope remain open.

The deterministic JSON object contains exactly:

- schema identity `tracktemplate.transition-state` and integer version `1`;
- one intent object with explicit `mm` and `rad` units, coordinate frame
  `canonical-local-left-turn-v1`, algorithm identity and tolerance-profile
  identity; and
- either no analytical result or one result containing the transition length,
  complete analysis-input signature and result-integrity signature.

Keys are serialised in deterministic lexical order with standard JSON numbers.
Duplicate fields, missing or unexpected canonical fields, non-standard numbers,
unknown schemas, unsupported versions, units, frames, algorithms and tolerance
profiles fail closed with a structured non-mutating diagnostic. No `Part`
shape, mesh, preview path or exact geometry is stored.

The tolerance profile identifies the exact accepted B15 behaviour:

| Rule | Value |
| --- | ---: |
| Zero-length geometry tolerance | `1e-8 mm` |
| Default Simpson integration steps | `240` |
| Maximum-length guard | `1e-6 mm` |
| Achievable-range slack | `1e-6 mm` |
| Endpoint residual | `1e-8 mm` |
| Bisection residual | `1e-10 mm` |
| Bisection interval | `1e-7 mm` |
| Maximum bisection iterations | `72` |

## Signature and dirty-state rules

The application layer is the one authoritative owner of transition signatures:

- the analysis signature includes all four numerical inputs, units, coordinate
  frame, algorithm identity and tolerance profile;
- stable identity and diagnostic labels are deliberately excluded because they
  do not change the successful numerical value;
- changing either diagnostic label retains a current successful result;
- changing any numerical input drops the result and records
  `analysis-invalidated`;
- changing the stable identity through replacement is rejected;
- analysis reuses the same immutable state object when its signatures are
  current; and
- a numerical A-B-A sequence recomputes on each numerical change and returns
  the exact original result/signatures after change-back.

The result-integrity signature covers the complete analysis signature, result
value and result unit. The writer refuses a stale or unverifiable result. The
reader preserves valid canonical intent but discards stale or damaged derived
analysis with the ordered finding `stale-analysis-discarded` or
`corrupt-analysis-discarded`. Therefore a damaged cache cannot become railway
truth and does not make valid intent unrecoverable.

## Source and dependency boundary

The new package locations are the minimum justified by this tranche:

- `tracktemplate.domain.transition` owns the immutable domain intent;
- `tracktemplate.application.transition_state` owns the application command,
  signatures, invalidation and adapter-neutral JSON contract; and
- `tracktemplate.api` remains the narrow migration façade.

The application layer depends inward on the two transition domain modules.
Neither domain nor application imports FreeCAD, Part, Qt, pivy or a third-party
package. The structural analyser now recognises this one real application
boundary; no adapter, presentation, UI or chair package tree has been created.

## Validation evidence

The tranche validator directly covers immutable records, exact numerical
result parity, deterministic cold and analysed round-trips, valid reuse,
every numerical input invalidation, label-only reuse, A-B-A change-back,
stable-identity rejection, signed-zero representation, stale/corrupt derived
result recovery, duplicate/missing/extra fields, unsupported schema versions,
non-finite inputs, structured diagnostics, isolated imports and dependency
direction.

Observed on 2026-07-22 from the repository root:

| Check | Result |
| --- | --- |
| Parse B14, B15, B16 launcher and all new/changed Python | Passed |
| Every `tests/validate_*.py` standalone validator | 33/33 passed |
| Dedicated Phase 4 canonical-state validator | Passed |
| Deterministic modular structure | Passed; declared application boundary, permitted inward edges, no cycle, forbidden domain dependency or warning |
| Isolated API/domain/application import with FreeCAD, Part, Qt and pivy blocked | Passed; no host import attempted |
| B15 FreeCAD 1.1 headless smoke | Passed |
| Accepted Phase 2 FreeCAD loading smoke | Passed |
| Retained Phase 3 FreeCAD routing smoke | Passed |
| Phase 4 FreeCAD 1.1 canonical-state smoke | Passed; exact round-trip and zero document mutation |

The dedicated qualified-FreeCAD smoke is intentionally limited to type/runtime
compatibility, exact JSON round-trip and zero document mutation; it is not
FreeCAD property, transaction, Undo/Redo or FCStd save/reopen evidence. No
real-GUI workflow or performance run is claimed because this tranche does not
alter an operator route, document, renderer, exact geometry or export path.

## Current Phase 4 gate disposition

| Exit condition | Current disposition |
| --- | --- |
| Selected-slice save/reopen without result or identity drift | Active: deterministic adapter-neutral round-trip exists; FreeCAD properties and FCStd save/reopen remain due |
| Exact parameter invalidation including cold/reuse/change-back | Active: transition analysis cases are directly tested; downstream preview, exact-validation and export propagation remain due |
| Undo/redo and failed updates leave a valid document | Pending: requires the FreeCAD adapter and one-command transaction boundary |
| Preview/exact geometry can be deleted and regenerated from canonical state | Pending: no Phase 5/6 renderer or exact adapter is being invented here |
| Deterministic, fail-closed chair-definition package | Pending: the cross-cutting schema must be defined before a production builder, with S1 evidence still blocked |
| Supported schema/version window agreed and tested | Active: exact transition v1 development reader/writer is tested; owner agreement and chair/legacy windows remain due |

## Remaining risks and next bounded tranche

- A JSON round-trip is not a FreeCAD save/reopen result. The next persistence
  tranche should add the smallest qualified-host adapter for this record,
  storing one compact property on a copied/disposable document and proving
  transaction, Undo/Redo, save/reopen and stale-result recovery.
- Stable identity generation and mapping to a logical FreeCAD object are not
  yet implemented. The adapter must not use object order or labels as identity.
- The B14/B15 detector and family-gated copied-target migration remain due. A
  transition-only adapter must not imply that a whole legacy document is
  migratable.
- Preview, exact-validation and export signatures cannot be completed until
  those derived-result contracts exist; adapters must not invent partial keys.
- The chair-definition schema and its rights/provenance fields remain a
  separate mandatory Phase 4 tranche before any production chair builder.
- The provisional v1 window requires explicit project-owner acceptance before
  it can satisfy the Phase 4 schema/version exit condition.
